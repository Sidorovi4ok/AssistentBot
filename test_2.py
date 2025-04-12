import torch
from transformers import (
    AutoTokenizer,
    AutoModelForQuestionAnswering,
    AutoModelForCausalLM,
    pipeline
)

class RuQAGenerator:
    def __init__(
        self,
        qa_model_name: str = "AlexKay/xlm-roberta-large-qa-multilingual-finedtuned-ru",
        # Меняем на более крупную модель генерации
        gen_model_name: str = "sberbank-ai/rugpt3medium_based_on_gpt2"
    ):
        # 1) Экстрактивный QA
        print(f"Loading QA model `{qa_model_name}`…")
        self.qa_tokenizer = AutoTokenizer.from_pretrained(qa_model_name)
        self.qa_model     = AutoModelForQuestionAnswering.from_pretrained(qa_model_name)

        # 2) Генеративная модель (ruGPT‑3 Medium вместо Small)
        print(f"Loading generation model `{gen_model_name}`…")
        self.gen_tokenizer = AutoTokenizer.from_pretrained(gen_model_name)
        self.gen_model     = AutoModelForCausalLM.from_pretrained(gen_model_name)

        # Устройство: GPU (0) или CPU (-1)
        self.device = 0 if torch.cuda.is_available() else -1

        # QA‑пайплайн
        self.qa_pipeline = pipeline(
            "question-answering",
            model=self.qa_model,
            tokenizer=self.qa_tokenizer,
            device=self.device
        )
        # Генеративный пайплайн
        self.gen_pipeline = pipeline(
            "text-generation",
            model=self.gen_model,
            tokenizer=self.gen_tokenizer,
            device=self.device,
            # для более «жесткого» контроля связности можно выключить семплинг:
            # do_sample=False, num_beams=4
            do_sample=True,
            temperature=0.8,
            top_p=0.9,
            max_new_tokens=100,
            pad_token_id=self.gen_tokenizer.eos_token_id
        )

        print("Обе модели загружены и готовы к работе!\n")

    def answer_and_expand(self, question: str, context: str) -> str:
        # 1) Чистый экстрактивный ответ
        qa_result = self.qa_pipeline(question=question, context=context)
        short_answer = qa_result["answer"]
        score = qa_result["score"]

        # 2) Формируем промпт для «обёртки»
        prompt = (
            f"Вопрос: {question}\n"
            f"Контекст: {context}\n"
            f"Краткий ответ: {short_answer}\n"
            f"Пояснение и дополнительные детали:"
        )

        # 3) Генерируем расширенный ответ
        gen_outputs = self.gen_pipeline(prompt, num_return_sequences=1)
        full_text = gen_outputs[0]["generated_text"]
        expanded = full_text[len(prompt):].strip()

        # 4) Финальный текст
        final = (
            f"Краткий ответ: «{short_answer}» (уверенность {score:.2f})\n\n"
            f"{expanded}"
        )
        return final

def main():
    assistant = RuQAGenerator()

    print("=== Интерактивный режим ===")
    print("Введите контекст (несколько строк, пустая строка — конец ввода), затем — вопрос.\n"
          "Чтобы выйти, оставьте контекст пустым.\n")

    while True:
        # ввод контекста
        lines = []
        print("=== Контекст ===")
        while True:
            line = input()
            if not line:
                break
            lines.append(line)
        context = " ".join(lines).strip()
        if not context:
            print("Контекст не введён — завершаем.")
            break

        # ввод вопроса
        question = input("\nВопрос: ").strip()
        if not question:
            print("Пустой вопрос — завершаем.")
            break

        # вывод ответа
        result = assistant.answer_and_expand(question, context)
        print("\n" + result)
        print("\n" + ("—" * 50) + "\n")

if __name__ == "__main__":
    main()
