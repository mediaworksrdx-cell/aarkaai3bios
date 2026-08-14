"""Reproduce the exact Turn 2 chicken tikka prompt and stream details."""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from modules import aarkaa_engine
import config

aarkaa_engine.init()

# The exact 2078 character biryani recipe from the first turn
biryani_recipe = """# Chicken Biryani Recipe

## Ingredients:
- 2 cups basmati rice
- 1 lb boneless chicken, cut into small pieces (or any other meat of your choice)
- 4 medium potatoes, peeled and cubed
- 3 large onions, sliced thin
- 2 tablespoons ginger-garlic paste
- 1/2 cup yogurt
- 1 teaspoon turmeric powder
- 2 teaspoons chili powder (adjust to taste)
- 1 tablespoon coriander powder
- 1 tablespoon cumin powder
- 1 tablespoon garam masala
- A pinch of saffron dissolved in warm milk (optional)
- Fresh cilantro and mint leaves, chopped
- Ghee or cooking oil
- Whole spices (bay leaf, cloves, cardamom pods, cinnamon stick)
- Salt to taste

## Instructions:

### Step 1: Rice Preparation
Wash the basmati rice thoroughly and soak it for 30 minutes. In a large pot, bring water to a boil. Add salt, whole spices, and the soaked rice. Cook the rice until it is 70-80% done (about 7-8 minutes). Drain and set aside.

### Step 2: Chicken Marinade
In a bowl, mix the chicken pieces with ginger-garlic paste, yogurt, turmeric powder, chili powder, coriander powder, cumin powder, garam masala, and salt. Marinate for at least 30 minutes.

### Step 3: Onion Caramelization
Heat oil or ghee in a deep pot. Fry the sliced onions until they are golden brown and caramelized. Remove half of the onions and set aside for layering.

### Step 4: Cooking the Chicken
In the same pot with the remaining onions and oil, add the marinated chicken. Cook over medium-high heat until the chicken is tender and cooked through (about 15 minutes).

### Step 5: Cooking the Potatoes
In a separate pan, fry the cubed potatoes in a little oil until they are golden brown and cooked through.

### Step 6: Layering the Biryani
In the pot with the cooked chicken, add a layer of the cooked potatoes. Next, add the cooked basmati rice on top. Sprinkle the reserved caramelized onions, chopped cilantro, mint leaves, and saffron milk over the rice.

### Step 7: Dum Cooking (Final Phase)
Cover the pot with a tight-fitting lid or seal it with dough to trap the steam. Cook on low heat (dum) for 15-20 minutes to allow the flavors to blend.

### Final Touches:
Remove the biryani from heat after it finishes cooking. Let it rest for a few minutes before serving.

Enjoy your homemade Chicken Biryani!"""

# Truncate to 1500 chars like _build_chatml_multi does
truncated_biryani = biryani_recipe[:1500] + "…"

history = [
    {"role": "user", "message": "how to make chicken biryani step by step"},
    {"role": "assistant", "message": truncated_biryani}
]

query = "how to make chicken tikka step by step"
context = ""  # No RAG candidates found for tikka

print("Building prompt...")
result = aarkaa_engine._build_final_prompt(query, context, intent="", lang="en", mode="production", history=history)
prompt, tokens, temp = result[0], result[1], result[2]

print(f"Prompt length: {len(prompt)} chars")
print(f"Max tokens: {tokens}")
print(f"Temperature: {temp}")
print("--- PROMPT START ---")
print(prompt)
print("--- PROMPT END ---\n")

print("Generating stream:")
generated_text = ""
stop_tokens = ["<|im_end|>", "<|im_start|>", "<|endoftext|>"]

stream = aarkaa_engine._model(
    prompt,
    max_tokens=tokens,
    temperature=temp,
    top_p=0.9,
    repeat_penalty=1.15,
    stop=stop_tokens,
    stream=True
)

for i, chunk in enumerate(stream):
    choice = chunk["choices"][0]
    token = choice["text"]
    finish_reason = choice.get("finish_reason")
    if token:
        generated_text += token
        print(token, end="", flush=True)
    if finish_reason:
        print(f"\n[STREAM FINISHED. Reason: {finish_reason}]")

print(f"\nTotal length: {len(generated_text)} chars")
