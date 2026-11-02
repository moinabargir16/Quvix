
from adaptive import update_difficulty

# Starting difficulty
difficulty = "Easy"
streak = 0

# True = Correct answer
# False = Incorrect answer
answers = [True, True, True, False, False]

print("===== QUVIX ADAPTIVE ALGORITHM TEST =====")

for i, answer in enumerate(answers, start=1):

    difficulty, streak = update_difficulty(
        difficulty,
        answer,
        streak
    )

    result = "Correct" if answer else "Incorrect"

    print(f"\nQuestion {i}: {result}")
    print("Current Difficulty:", difficulty)
    print("Correct Answer Streak:", streak)

print("\n===== TEST COMPLETED =====")
