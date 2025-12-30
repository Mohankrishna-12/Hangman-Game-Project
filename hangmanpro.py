import tkinter as tk
import random
import requests
import os
import winsound
import threading

# ================= CONFIG =================
MAX_HANGMAN_PARTS = 6
sound_enabled = True
music_playing = False

# ================= SOUND =================
def play_beep(freq, dur):
    if sound_enabled:
        try:
            winsound.Beep(freq, dur)
        except:
            pass

def play_music():
    global music_playing
    if sound_enabled and not music_playing:
        music_playing = True
        def loop():
            while sound_enabled:
                try:
                    winsound.PlaySound("bg_music.wav", winsound.SND_FILENAME)
                except:
                    break
        threading.Thread(target=loop, daemon=True).start()

def stop_music():
    global music_playing
    music_playing = False
    winsound.PlaySound(None, winsound.SND_PURGE)

# ================= HIGH SCORE =================
def load_high_score():
    if os.path.exists("highscore.txt"):
        return int(open("highscore.txt").read())
    return 0

def save_high_score(score):
    open("highscore.txt", "w").write(str(score))

# ================= RANDOM WORD =================
def get_random_word(min_len, max_len):
    try:
        length = random.randint(min_len, max_len)
        url = f"https://random-word-api.herokuapp.com/word?number=1&length={length}"
        return requests.get(url, timeout=3).json()[0].lower()
    except:
        return random.choice(["python", "computer", "developer", "algorithm"])

# ================= GAME CLASS =================
class HangmanGame:
    def __init__(self, root):
        self.root = root
        self.root.title("Hangman – Final Version")
        self.root.geometry("900x650")
        self.root.configure(bg="#121212")
        self.root.resizable(False, False)

        self.score = 0
        self.high_score = load_high_score()
        self.difficulty = tk.StringVar(value="Easy")
        self.sound_var = tk.BooleanVar(value=True)

        self.build_ui()
        play_music()

    # ---------------- UI ----------------
    def build_ui(self):
        tk.Label(self.root, text="🎮 HANGMAN GAME",
                 font=("Segoe UI", 22, "bold"),
                 bg="#121212", fg="#00E676").pack(pady=10)

        top = tk.Frame(self.root, bg="#121212")
        top.pack()

        tk.Label(top, text="Difficulty:", bg="#121212", fg="white").grid(row=0, column=0)
        tk.OptionMenu(top, self.difficulty, "Easy", "Medium", "Hard").grid(row=0, column=1)

        tk.Button(top, text="Start", command=self.start_game,
                  bg="#1E88E5", fg="white", width=8).grid(row=0, column=2, padx=5)

        tk.Button(top, text="Restart", command=self.restart_game,
                  bg="#FB8C00", fg="black", width=8).grid(row=0, column=3, padx=5)

        tk.Checkbutton(top, text="Sound", variable=self.sound_var,
                       command=self.toggle_sound,
                       bg="#121212", fg="white",
                       selectcolor="#121212").grid(row=0, column=4, padx=10)

        self.word_label = tk.Label(self.root, font=("Consolas", 28),
                                   bg="#121212", fg="white")
        self.word_label.pack(pady=20)

        self.status_label = tk.Label(self.root, font=("Segoe UI", 13),
                                     bg="#121212", fg="#B0BEC5")
        self.status_label.pack()

        score_frame = tk.Frame(self.root, bg="#121212")
        score_frame.pack()

        self.score_label = tk.Label(score_frame, text="Score: 0",
                                    bg="#121212", fg="#4FC3F7")
        self.score_label.pack(side="left", padx=20)

        self.high_label = tk.Label(score_frame,
                                   text=f"High Score: {self.high_score}",
                                   bg="#121212", fg="#FFD54F")
        self.high_label.pack(side="right", padx=20)

        self.entry = tk.Entry(self.root, font=("Segoe UI", 16), justify="center")
        self.entry.pack(pady=10)
        self.entry.bind("<Return>", lambda e: self.guess_letter())

        tk.Button(self.root, text="Guess Letter",
                  command=self.guess_letter,
                  bg="#43A047", fg="white", width=15).pack()

        self.canvas = tk.Canvas(self.root, width=320, height=380,
                                bg="#1E1E1E", highlightthickness=0)
        self.canvas.pack(pady=20)

    # ---------------- SOUND TOGGLE ----------------
    def toggle_sound(self):
        global sound_enabled
        sound_enabled = self.sound_var.get()
        if sound_enabled:
            play_music()
        else:
            stop_music()

    # ---------------- GAME START ----------------
    def start_game(self):
        level = self.difficulty.get()

        if level == "Easy":
            self.word = get_random_word(4, 6)
        elif level == "Medium":
            self.word = get_random_word(6, 8)
        else:
            self.word = get_random_word(8, 10)

        self.guessed = []
        self.wrong = 0
        self.game_over = False
        self.entry.config(state="normal")

        self.canvas.delete("all")
        self.draw_base()
        self.update_display()
        self.status_label.config(text="Game Started!")

    def restart_game(self):
        self.score = 0
        self.score_label.config(text="Score: 0")
        self.start_game()

    # ---------------- DISPLAY ----------------
    def update_display(self):
        display = " ".join([c if c in self.guessed else "_" for c in self.word])
        self.word_label.config(text=display)

        if "_" not in display and not self.game_over:
            play_beep(1200, 400)
            self.score += 40
            self.game_over = True
            self.status_label.config(text="🎉 YOU WON!")
            self.entry.config(state="disabled")
            self.update_scores()

    # ---------------- GUESS ----------------
    def guess_letter(self):
        if self.game_over:
            return

        guess = self.entry.get().lower()
        self.entry.delete(0, tk.END)

        if not guess.isalpha() or len(guess) != 1:
            self.status_label.config(text="Enter ONE letter only")
            return

        if guess in self.guessed:
            self.status_label.config(text="Already guessed")
            return

        self.guessed.append(guess)

        if guess in self.word:
            play_beep(900, 120)
            self.score += 8
            self.status_label.config(text="Correct!")
        else:
            play_beep(400, 200)
            self.score -= 3
            self.wrong += 1
            self.animate_draw()

            # 🔴 END GAME WHEN HANGMAN COMPLETE
            if self.wrong >= MAX_HANGMAN_PARTS:
                self.game_over = True
                self.entry.config(state="disabled")
                self.status_label.config(text="💀 GAME OVER")
                self.animate_word_reveal()
                self.update_scores()
                return

        self.update_scores()
        self.update_display()

    # ---------------- WORD REVEAL ----------------
    def animate_word_reveal(self):
        self.reveal_index = 0
        self.word_label.config(text="_ " * len(self.word))
        self.root.after(200, self.reveal_step)

    def reveal_step(self):
        if self.reveal_index < len(self.word):
            text = ""
            for i in range(len(self.word)):
                text += self.word[i] + " " if i <= self.reveal_index else "_ "
            self.word_label.config(text=text)
            self.reveal_index += 1
            self.root.after(180, self.reveal_step)
        else:
            self.status_label.config(text=f"💀 GAME OVER | Word: {self.word}")

    # ---------------- SCORES ----------------
    def update_scores(self):
        if self.score > self.high_score:
            self.high_score = self.score
            save_high_score(self.high_score)
            self.high_label.config(text=f"High Score: {self.high_score}")

        self.score_label.config(text=f"Score: {self.score}")

    # ---------------- DRAWING ----------------
    def draw_base(self):
        self.canvas.create_line(50, 350, 270, 350, width=4, fill="#90CAF9")
        self.canvas.create_line(90, 350, 90, 50, width=4, fill="#90CAF9")
        self.canvas.create_line(90, 50, 220, 50, width=4, fill="#90CAF9")
        self.canvas.create_line(220, 50, 220, 90, width=4, fill="#90CAF9")

    def animate_draw(self):
        parts = [
            lambda: self.canvas.create_oval(190, 90, 250, 150, width=4, outline="#EF5350"),
            lambda: self.canvas.create_line(220, 150, 220, 240, width=4, fill="#FF7043"),
            lambda: self.canvas.create_line(220, 170, 180, 200, width=4, fill="#FFD54F"),
            lambda: self.canvas.create_line(220, 170, 260, 200, width=4, fill="#FFD54F"),
            lambda: self.canvas.create_line(220, 240, 190, 310, width=4, fill="#66BB6A"),
            lambda: self.canvas.create_line(220, 240, 250, 310, width=4, fill="#66BB6A"),
        ]

        if self.wrong <= len(parts):
            self.root.after(120, parts[self.wrong - 1])

# ================= RUN =================
root = tk.Tk()
HangmanGame(root)
root.mainloop()
