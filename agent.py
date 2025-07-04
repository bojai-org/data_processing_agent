from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
import re
import json
from processor import YourDataProcessor


class PromptError(Exception):
    pass

class WriteError(Exception):
    pass

class ImplementationError(Exception):
    pass

class DescriptionError(Exception):
    pass


class DataProcessorAgent:
    def __init__(self, address, data_dir, model_name="llama2") -> None:
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(model_name)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)
        self.address = address
        self.data_dir = data_dir

    def process(self, description, image):
        max_tries = 3
        tries = 0
        while tries < max_tries:
            try:
                answer = self.ask_local_model(description, image)
                self.write_function(answer)
                self.test_function()
                return
            except (PromptError, WriteError, ImplementationError) as e:
                tries += 1
                if tries >= max_tries:
                    raise DescriptionError(
                        "The LLM was unable to implement your function. Try changing the description or implement it yourself."
                    ) from e

    def write_function(self, reply):
        match = re.search(r"```(?:python)?\s*(.*?)```", reply, re.DOTALL)
        if match:
            function_text = match.group(1).strip()
        else:
            raise PromptError("Prompt did not output a function.")

        try:
            with open(self.address, 'r', encoding='utf-8') as f:
                original_code = f.read()

            pattern = r"(^[ \t]*)def get_inputs_outputs\s*\(self,\s*data_dir\):(?:\n(?:\1 {4}.*|\1\t.*)*)?"
            match = re.search(pattern, original_code, re.MULTILINE)
            if not match:
                raise WriteError("Existing function not found in the code file.")

            indent = match.group(1)
            old_func_block = match.group(0)

            # Re-indent the new function
            if function_text.startswith("def get_inputs_outputs"):
                lines = function_text.splitlines()
                new_func_def = '\n'.join(indent + line if line.strip() else '' for line in lines)
            else:
                body = '\n'.join(indent + '    ' + line if line.strip() else '' for line in function_text.splitlines())
                new_func_def = f"{indent}def get_inputs_outputs(self, data_dir):\n{body}"

            updated_code = original_code.replace(old_func_block, new_func_def, 1)

            with open(self.address, 'w', encoding='utf-8') as f:
                f.write(updated_code)

        except Exception as e:
            raise WriteError(f"Error writing the function: {e}")

    def test_function(self):
        processor = YourDataProcessor(self.data_dir, [0.5, 0.5], self.model, None, self.tokenizer)
        try:
            processor.get_item_untokenized(0)
        except Exception as e:
            raise ImplementationError(e)

    def ask_local_model(self, description, image):
        prompt = f'''
            You are a precise developer who can write data processors well. You are asked to code the initial part of data processing. Carefully follow instructions below.

            Here is my data address: data_dir

            Here is how my data is structured:
            {description}

            {"Images are involved; the outputs list is just the address of each image." if image else ""}

            If you use any import statements, import them inside the function definition. 

            The function should look like this, do not include the class definition, just the function: 

            def get_inputs_outputs(self, data_dir): 
                import x 
                from x import y 
                # function body
        '''

        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
        output = self.model.generate(**inputs, max_new_tokens=300, do_sample=True, temperature=0.7)
        generated = output[0][inputs['input_ids'].shape[1]:]  # remove prompt from output
        decoded_output = self.tokenizer.decode(generated, skip_special_tokens=True)
        return decoded_output
