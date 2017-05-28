import argparse
from collections import defaultdict, Counter, deque
import random
import json
import time
from tqdm import tqdm
import wikipedia


class MarkovModel(object):
    def __init__(self):
        self.states = defaultdict(lambda: Counter())
        self.totals = Counter()

    def add_sample(self, state, followup):
        self.states[state][followup] += 1
        self.totals[state] += 1

    def generate(self):
        result = []
        for followup in self.iter_chain():
            result.append(followup)
        return result

    def iter_chain(self, state=tuple()):
        while state in self.states:
            followup = self.next(state)
            state = state[1:] + followup
            for token in followup:
                yield token

    def next(self, state):
        r = random.randint(0, self.totals[state] - 1)
        for followup, weight in self.states[state].items():
            r -= weight
            if r < 0:
                return followup
        raise ValueError("Mismatch of totals / weights for state {}".format(state))

    def to_json(self):
        converted = {' '.join(state): list(followups.keys()) for state, followups in self.states.items()}
        return json.dumps(converted)


def iter_states(tokens, state_size, start_state=tuple(), end_marker=None):
    # First transition is from empty state to first token-based state
    yield start_state, tuple(tokens[0:state_size])
    state = tuple(tokens[0:state_size])
    for token in tokens[state_size:]:
        # Each additional token means last state to that token
        yield state, (token,)
        # New state is last {state_size} tokens we yielded
        state = state[1:] + (token,)
    # End is marked by None
    yield state, end_marker


def tokenize_story(story):
    story = deque(story)
    yield "\n"
    while len(story) > 0:
        token = eat_one_token(story)
        if token is not None:
            yield token


def eat_one_token(story):
    while len(story) > 0 and isinvalid(story[0]):
        story.popleft()
    if len(story) == 0:
        return None
    if isalnum(story[0]):
        return eat_word(story)
    if ispunctuation(story[0]):
        return eat_punctuation(story)
    if isnewline(story[0]):
        return eat_newline(story)


def isinvalid(char):
    return not isalnum(char) and not ispunctuation(char) and not isnewline(char)


def isalnum(char):
    return char.isalnum() or char == "'" or char == "’"


def ispunctuation(char):
    return char in ",.-!?:&"


def isnewline(char):
    return char == '\n'


def eat_word(story):
    word = [story.popleft()]
    while len(story) > 0 and isalnum(story[0]):
        word.append(story.popleft())
    return ''.join(word)


def eat_punctuation(story):
    token = [story.popleft()]
    while len(story) > 0 and ispunctuation(story[0]):
        token.append(story.popleft())
    return ''.join(token)


def eat_newline(story):
    while len(story) > 0 and story[0].isspace():
        story.popleft()
    return '\n'


def load_story(filenames):
    stories = []
    for filename in filenames:
        with open(filename) as fp:
            story = fp.read()
            if filename.endswith('.ftxt'):
                story = remove_single_newlines(story)
            stories.append(story)
    return '\n'.join(stories)


def remove_single_newlines(story):
    paragraphs = [[]]
    for line in story.splitlines():
        if len(line.strip()) == 0:
            paragraphs.append([])
        else:
            paragraphs[-1].append(line)
    return '\n'.join(' '.join(x for x in p) for p in paragraphs)


def load_wikipedia(num_articles):
    lines = []
    while num_articles > 0:
        chunk = min(10, num_articles)
        num_articles -= 10
        for article in wikipedia.random(chunk):
            try:
                page = wikipedia.page(article)
            except wikipedia.DisambiguationError as ex:
                page = wikipedia.page(ex.args[1][0])
            print(article)
            lines.extend(x for x in page.content.splitlines() if not x.startswith('==') and len(x) > 0)
    return '\n'.join(lines)


def main(args):
    model = MarkovModel()

    if args.mode == 'txt':
        story = load_story(args.txt)
    elif args.mode == 'wikipedia':
        story = load_wikipedia(100)
    else:
        raise ValueError("invalid mode {}".format(args.mode))

    tokens = list(tqdm(tokenize_story(story), desc="tokenizing"))
    for state, followup in tqdm(iter_states(tokens, 3, start_state=tuple('\n'), end_marker=()), desc="building model"):
        model.add_sample(state, followup)

    print("Saving Model...")
    with open("model.json", "w") as fp:
        fp.write(model.to_json())

    print("Generating Story:")
    for token in model.iter_chain(tuple('\n')):
        if not ispunctuation(token):
            print(" ", end="")
        print(token, end="", flush=True)
        time.sleep(0.05)


def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument('mode', choices=['txt', 'wikipedia'])
    ap.add_argument('--txt', action='append')
    return ap.parse_args()

if __name__ == '__main__':
    main(parse_args())
