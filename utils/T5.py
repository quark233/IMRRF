from transformers import T5Tokenizer, T5ForConditionalGeneration
import torch
from utils.prompt import VERIFY_CLAIM

class T5_Question_Answering:
    def __init__(self):
        # Initialize the tokenizer
        self.tokenizer = T5Tokenizer.from_pretrained("flan-t5-xl_path")

        # Initialize the model
        self.model = T5ForConditionalGeneration.from_pretrained("flan-t5-xl_path")

        # If using multiple GPUs and if your environment supports it, parallelize the model
        try:
            self.model.parallelize()
        except AttributeError:
            print("parallelize method not available or not supported in this environment")

    def generate(self, input_string, **generator_args):
        device = "cuda:0" if torch.cuda.is_available() else "cpu"
        input_ids = self.tokenizer.encode(input_string, return_tensors="pt").to(device)
        with torch.no_grad():
            res = self.model.generate(input_ids, **generator_args)
        return self.tokenizer.batch_decode(res, skip_special_tokens=True)
    

    def verify_claim(self, claim, summary, llm_evidence):
        prompt = VERIFY_CLAIM.format(claim=claim, summary=summary, llm_evidence=llm_evidence)
        predict_answer = {}
        answer_text = self.generate(prompt,
                    max_length = None,
                    max_new_tokens = 8)[0].strip()
        predict_answer['rationale'] = ""
        predict_answer['answer_text'] = answer_text

        return predict_answer