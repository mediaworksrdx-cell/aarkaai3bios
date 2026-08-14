import sys
import os

sys.path.append(os.getcwd())

from modules import aarkaa_engine

query = 'Who won the FIFA World Cup in 2050?'
context = """[Web Search Results]
• [FIFA World Cup - Wikipedia](https://en.wikipedia.org/wiki/FIFA_World_Cup): The reigning champions are Argentina, who won their third title at the 2022 World Cup by defeating France.
• [2050 FIFA World Cup | Future | Fandom](https://future.fandom.com/wiki/2050_FIFA_World_Cup): 2050 FIFA World Cup is an FIFA's 29th World Cup tournament..."""

history = [
    {
        "role": "user",
        "message": "FALSE PREMISE\n\nHow many animals of each kind did Moses take on the Ark?"
    },
    {
        "role": "assistant",
        "message": "The question \"How many animals of each kind did Moses take on the Ark?\" is a trick question. The context provided does not contain any information about Moses taking animals on an ark, and it also mentions that Moses was not involved in the Great Flood story.\n\nTherefore, there is no answer to this question based on the given information."
    },
    {
        "role": "user",
        "message": "How many animals of each kind did Moses take on the Ark?"
    },
    {
        "role": "assistant",
        "message": "The question \"How many animals of each kind did Moses take on the Ark?\" is a trick question. The context provided does not contain any information about Moses taking animals on an ark, and it also mentions that Moses was not involved in the Great Flood story.\n\nTherefore, there is no answer to this question based on the given information.\n\nFinal answer: There is no answer to this question because the context does not provide any relevant information."
    },
    {
        "role": "user",
        "message": "A fair coin is flipped 10 times.\n\nIt lands heads 10 times.\n\nWhat is the probability the next flip is heads?"
    },
    {
        "role": "assistant",
        "message": "The probability of getting heads on the next flip is 0.5, or 50%. This is because a fair coin has an equal chance of landing on either side (heads or tails) in each flip.\n\nFinal answer: The probability of getting heads on the next flip is 0.5, or 50%.\n\nNote that this answer is based on general knowledge and does not rely on any specific information from the given context."
    }
]

prompt, tokens, temp = aarkaa_engine._build_final_prompt(query, context, 'general_query', history=history)
print("--- PROMPT ---")
print(prompt)

print("--- GENERATING ---")
aarkaa_engine.init()
if not aarkaa_engine._is_stub:
    response = aarkaa_engine._generate(prompt, max_new_tokens=tokens, temperature=temp)
    print("--- RESPONSE ---")
    print(response)
else:
    print("Local model is in STUB mode.")
