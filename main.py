import requests
import datetime
import random
import re


def get_definition(word):
    response = requests.get(f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}")
    data = response.json()
    try:
        definition = data[0]['meanings'][0]['definitions'][0]['definition']
    except KeyError:
        definition = get_gpt_definition(word)
    return definition


def get_gpt_definition(word):
    # Use the OpenAI API to get the definition
    api_key = ''
    response = requests.post(
        "https://api.openai.com/v1/completions",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        },
        json={
            "prompt": f"Imagine you are dictionary for B1 english learners. Define the term '{word}'.",
            "model": 'text-davinci-002',
            "max_tokens": 100,
            "temperature": 0.1,
            "n": 1
        }
    )
    with open('gpt_response.txt', 'w', encoding='utf-8') as f:
        f.write(response.text)
    response_data = response.json()
    definition = response_data['choices'][0]['text'].strip()
    # Replace the word with asterisks in the definition, case-insensitive
    asterisks = '*' * len(word)
    definition = re.sub(re.compile(re.escape(word), re.IGNORECASE), asterisks, definition)
    return definition


def get_next_review_date(word):
    with open('words_to_review.txt', 'r+') as f:
        for line in f:
            if word in line:
                if ',' in line:
                    next_review_date = datetime.datetime.strptime(line.strip().split(',')[1], '%Y-%m-%d').date()
                    return next_review_date
                else:
                    break
    return None

# Calculate the next review date for a word
def calculate_next_review_date(num_hidden_letters):
    days_to_wait = num_hidden_letters + 1
    return (datetime.datetime.now() + datetime.timedelta(days=days_to_wait)).strftime('%Y-%m-%d')


def update_review_date(word, next_review_date):
    with open('words_to_review.txt', 'r+') as f:
        lines = f.readlines()
        f.seek(0)
        for line in lines:
            if line.startswith(word):
                f.write(f"{word},{next_review_date}\n")
            else:
                f.write(line)
        f.truncate()
    return next_review_date


def review_words(words, max_words=30):
    random.shuffle(words)
    count = 0
    for word in words:
        if count >= max_words:
            break
        word = word.strip()
        word = word.split(',')[0]
        next_review_date = get_next_review_date(word)
        if next_review_date is None:
            next_review_date = datetime.date.today()
            update_review_date(word, next_review_date)
        elif next_review_date > datetime.date.today():
            continue
        definition = get_definition(word)
        print(f"What does this definition mean? '{definition}'")
        guessed_word = input("Enter the word that matches the definition: ")
        correct_guess = guessed_word.lower() == word.lower()
        hidden_word = word[0] + '*' * (len(word) - 1)
        num_hidden_letters = len(word) - 1
        while not correct_guess:
            print(f"Sorry, the correct word is '{hidden_word}'.")
            if num_hidden_letters > 0:
                num_hidden_letters -= 1
                hidden_word = word[0] + '*' * num_hidden_letters + word[-(len(word)-num_hidden_letters-1):]
            guessed_word = input("Enter the word that matches the definition: ")
            correct_guess = guessed_word.lower() == word.lower()
            if correct_guess:
                print("Correct! Good job!")
            else:
                print("Let's try again!")
        next_review_date = update_review_date(word, calculate_next_review_date(num_hidden_letters))
        print('The next review date: ')
        print(update_review_date(word, next_review_date))


if __name__ == '__main__':
    with open('words_to_review.txt', 'r') as f:
        words = [line.strip() for line in f.readlines()]
    review_words(words)
    input("No more words for the game")
