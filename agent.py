from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
import ollama
import re


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
        self.tokenizer = None
        self.model = model_name
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.address = address
        self.data_dir = data_dir

    def process(self, description, image):
        max_tries = 3
        tries = 0
        feedback = ""
        while tries < max_tries:
            try:
                answer = self.ask_local_model(description, image, feedback)
                new_func_def = self.write_function(answer)
                self.test_function()
                return
            except (PromptError, WriteError) as e:
                tries += 1
                if tries >= max_tries:
                    raise DescriptionError(
                        "The LLM was unable to implement your function. Try changing the description or implement it yourself."
                    ) from e
            except Exception as e: 
                tries += 1
                feedback = f"your previous implementation: {new_func_def} is wrong, here is the error: {str(e)}"
                print(e)
                if tries < max_tries:
                    print("trying again...")

    def write_function(self, reply):
        match = re.search(r"```(?:python)?\s*(.*?)```", reply, re.DOTALL)
        new_func_def = ""
        if match:
            function_text = match.group(1).strip()
        else:
            raise PromptError("Prompt did not output a function.")

        try:
            with open(self.address, 'r', encoding='utf-8') as f:
                original_code = f.read()

            # Match full function including its indented body
            pattern = (
                r"(^[ \t]*)def get_inputs_outputs\s*\(self,\s*data_dir\):"
                r"(?:\n(?:\1(?:    |\t).*)*)?"
            )
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

            return new_func_def

        except Exception as e:
            raise WriteError(f"Error writing the function: {e}")


    def test_function(self):
        from custom_data_processor import YourDataProcessor
        processor = YourDataProcessor(self.data_dir, [0.5, 0.5], self.model, None, self.tokenizer)
        try:
            processor.get_item_untokenized(0)
        except Exception as e:
            raise ImplementationError(e)

    def ask_local_model(self, description, image, feedback):
        prompt = f'''
            You are a precise developer who can write data processors well. You are asked to code the initial part of data processing. Carefully follow instructions below.

            Here is how my data is structured:
            {description}

            Write a function get_inputs_outputs(self, data_dir) that returns the needed inputs and outputs from my data as described above. Make it return two lists inputs, outputs. 

            {"Images are involved; the outputs list is just the address of each image." if image else ""} 

            If you use any import statements, import them inside the function definition. Use the simplest way possible to implement, only import libraries that are absolutely needed. 

            Return the function in a .md python code block python``` code ```. The function should look like this, do not include the class definition, just the function: 

            python ```
            def get_inputs_outputs(self, data_dir): 
                import x 
                from x import y 
                # function body
                # your code here use data_dir parameter to read based on description above
                inputs = # your code
                outputs = # your code
                # your code
                return inputs, outputs
            ```

            {feedback}
        '''

        response = ollama.chat(
            model=self.model,
            messages=[{"role": "user", "content": prompt}]
        )
        return response['message']['content']
    

## Initial simple testing
agent = DataProcessorAgent("custom_data_processor.py", "test_data.txt")
agent.process("The data_dir is a txt file, the txt file in each line there is the input then comma then the output. Ex: how are you?, I am fine.", False)