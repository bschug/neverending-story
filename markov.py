from collections import defaultdict, Counter, deque
import random
import json
import time
from tqdm import tqdm


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


def main():
    model = MarkovModel()
    with open('story.txt') as fp:
        story = fp.read()

    tokens = list(tqdm(tokenize_story(story), desc="tokenizing"))
    #token_to_id = {t: i for i, t in enumerate(tokens)}
    #id_to_token = {i: t for t, i in token_to_id.items()}

    #tokens = [token_to_id[t] for t in tokens]

    for state, followup in tqdm(iter_states(tokens, 3, start_state=tuple('\n'), end_marker=tuple()), desc="building model"):
        model.add_sample(state, followup)

    print("Saving Model...")
    with open("model.json", "w") as fp:
        fp.write(model.to_json())
    #with open("tokens.json", "w") as fp:
    #    fp.write(json.dumps(id_to_token))

    print("Generating Story:")
    for token in model.iter_chain(tuple('\n')):
    #    token = id_to_token[token]
        if not ispunctuation(token):
            print(" ", end="")
        print(token, end="", flush=True)
        time.sleep(0.2)


if __name__ == '__main__':
    main()