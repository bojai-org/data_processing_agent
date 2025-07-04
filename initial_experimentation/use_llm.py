import ollama
import openai
import re 
import json

# Set your OpenAI API key here
openai.api_key = "YOUR_API_KEY"

def ask_local_model(prompt, model="llama2"):
    response = ollama.chat(
        model=model,
        messages=[{"role": "user", "content": prompt}]
    )
    return response['message']['content']

promptu = f'''
Here is my data address: ./C:/data/
inside the data folder there is an images folder contianing images and a txt file containing tags for these images. The images are numberred 0 to len(images) and each line in the txt corresponds to an image. 

Write a function get_inputs_outputs(self, data_address) that returns the needed inputs and outputs from my data as described above. Make it return two lists inputs, outputs. 

Images are involved, the outputs list is just the address of each image.

If you use any import statements, import them inside the function definition before. So something like this: 
def get_inputs_outputs(self, data_address): 
    import x 
    from x import y 
    funciton definition as normal
'''


promptu = '''
Here is my data address: ./C:/data/
inside the data folder there is an images folder contianing images and a txt file containing tags for these images. The images are numberred 0 to len(images) and each line in the txt corresponds to an image. 

Write only the python function  
def __getitem__(self, idx) :
    untokenized_input = self.inputs[idx]
    untokenized_output = self.outputs[idx]

    #tokenize them according to logic below and return them in a tuple


that I will put in the class, returns tokenized tuple of input and output at idx. 

You already have a self.inputs and a self.outputs with untokenized data. Input is an address to an image, open it with PIL and return it embedded, and the text return embedded through passing the output item through the self.tokenizer, just self.tokenizer(item).

If you use any import statements, import them inside the function definition before. So something like this: 
def get_inputs_outputs(self, data_address): 
    import x 
    from x import y 
    funciton definition as normal

Only output the full __getitem__ function including the defintion above NOT the whole class. 

'''
reply = ask_local_model(promptu)
print(reply)

start = reply.find('python')
end = reply.rfind('')

if start != -1 and end != -1 and start < end:
    json_str = reply[start:end+1]
    try:
        data = json.loads(json_str)
        with open('test.json', 'w') as file:
            json.dump(data, file, indent=4)
    except json.JSONDecodeError:
        print("Invalid JSON format.")
else:
    print("No JSON found.")

