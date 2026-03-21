import random

_QUOTES = [
    ("The unexamined life is not worth living.", "Socrates"),
    ("We are what we repeatedly do. Excellence, then, is not an act, but a habit.", "Aristotle"),
    ("He who fears death will never do anything worthy of a living man.", "Seneca"),
    ("It is not death that a man should fear, but he should fear never beginning to live.", "Marcus Aurelius"),
    ("The happiness of your life depends upon the quality of your thoughts.", "Marcus Aurelius"),
    ("You have power over your mind, not outside events. Realize this, and you will find strength.", "Marcus Aurelius"),
    ("Waste no more time arguing about what a good man should be. Be one.", "Marcus Aurelius"),
    ("The obstacle is the way.", "Marcus Aurelius"),
    ("If it is not right, do not do it; if it is not true, do not say it.", "Marcus Aurelius"),
    ("Dwell on the beauty of life. Watch the stars, and see yourself running with them.", "Marcus Aurelius"),
    ("Make the best use of what is in your power, and take the rest as it happens.", "Epictetus"),
    ("Seek not the good in external things; seek it in yourselves.", "Epictetus"),
    ("First say to yourself what you would be; and then do what you have to do.", "Epictetus"),
    ("Man is not worried by real problems so much as by his imagined anxieties about real problems.", "Epictetus"),
    ("Luck is what happens when preparation meets opportunity.", "Seneca"),
    ("Omnia aliena sunt, tempus tantum nostrum est. (Everything else belongs to others, time alone is ours.)", "Seneca"),
    ("It is not that I'm so smart; it's just that I stay with problems longer.", "Albert Einstein"),
    ("The more I learn, the more I realize how much I don't know.", "Albert Einstein"),
    ("In the middle of difficulty lies opportunity.", "Albert Einstein"),
    ("Man is condemned to be free.", "Jean-Paul Sartre"),
    ("Hell is other people.", "Jean-Paul Sartre"),
    ("Existence precedes essence.", "Jean-Paul Sartre"),
    ("God is dead. God remains dead. And we have killed him.", "Friedrich Nietzsche"),
    ("Without music, life would be a mistake.", "Friedrich Nietzsche"),
    ("That which does not kill us makes us stronger.", "Friedrich Nietzsche"),
    ("He who has a why to live can bear almost any how.", "Friedrich Nietzsche"),
    ("The secret for harvesting from existence the greatest fruitfulness is — to live dangerously.", "Friedrich Nietzsche"),
    ("I think, therefore I am.", "René Descartes"),
    ("The only true wisdom is in knowing you know nothing.", "Socrates"),
    ("Wonder is the beginning of wisdom.", "Socrates"),
    ("Education is the kindling of a flame, not the filling of a vessel.", "Socrates"),
    ("At his best, man is the noblest of all animals; separated from law and justice he is the worst.", "Aristotle"),
    ("Knowing yourself is the beginning of all wisdom.", "Aristotle"),
    ("The more you know, the more you know you don't know.", "Aristotle"),
    ("Give me a place to stand and I will move the world.", "Archimedes"),
    ("To be is to be perceived.", "George Berkeley"),
    ("The life of man is solitary, poor, nasty, brutish, and short.", "Thomas Hobbes"),
    ("I am not an Athenian or a Greek, but a citizen of the world.", "Diogenes"),
    ("No man ever steps in the same river twice.", "Heraclitus"),
    ("Everything flows.", "Heraclitus"),
    ("The measure of intelligence is the ability to change.", "Albert Einstein"),
    ("Doubt is the origin of wisdom.", "René Descartes"),
    ("All that we see or seem is but a dream within a dream.", "Edgar Allan Poe"),
    ("The greatest remedy for anger is delay.", "Seneca"),
    ("Difficulty is what wakes up the genius.", "Nassim Nicholas Taleb"),
]


def get_quote() -> dict:
    """Return a random philosophy quote as {text, author}."""
    text, author = random.choice(_QUOTES)
    return {"text": text, "author": author}


def format_quote() -> str:
    q = get_quote()
    return f'"{q["text"]}"\n\n— {q["author"]}'
