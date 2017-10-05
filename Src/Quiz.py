import os
import sys
import random
import subprocess
import textwrap
import re
import glob
import cmd

class TerminalString:
   PURPLE = '\033[95m'
   CYAN = '\033[96m'
   DARKCYAN = '\033[36m'
   BLUE = '\033[94m'
   GREEN = '\033[92m'
   YELLOW = '\033[93m'
   RED = '\033[91m'
   BOLD = '\033[1m'
   UNDERLINE = '\033[4m'
   END = '\033[0m'

   def bold(self, string):
       return self.BOLD + string + self.END

# Parse command line arguments and determine the markdown file to be used
if len(sys.argv) == 1:
    md_files = glob.glob('*.md')
    if md_files:
        md_filename = md_files[0]
    else:
        print('No markdown (*.md) files found in the current directory')
        quit()
elif len(sys.argv) == 2:
    md_filename = sys.argv[1]
    if not md_filename.endswith('.md') :
        print(md_filename + 'is not a markdown (*.md) file.')
        quit()
    elif not os.path.isfile(md_filename):
        print('Could not find ' + md_filename + ' in the current directory.')
        quit()
else:
    print('Quiz: too many arguments.')
    print('Quiz requires either a markdown-file as the only argument,')
    print('or if no arguments are given, at least one markdown file (*.md)')
    print('has to be present in the current directory.')
    quit()

def clear_screen():
    dummy = subprocess.call('clear',shell=True)  # assignment to variable prevents printing of '0'

def terminal_width():
    return int(subprocess.check_output(['tput', 'cols']))

class QuizItem:
    def __init__(self, question, answer):
        self.question = question
        self.answer = answer
        self.correct_answer_count = 0
        self.wrong_answer_count = 0

    @property
    def practice_count(self):
        return self.correct_answer_count + self.wrong_answer_count

class QuizItemDeck:
    def __init__(self, quiz_items):
        self.quiz_items = quiz_items
        self.original_size = len(quiz_items)
        self.all_quiz_items = list(quiz_items)

    def next(self):
        if self.quiz_items:
            return self.quiz_items.pop(0)
        else:
            return None

    def return_quiz_item(self, quiz_item):
        if quiz_item not in self.quiz_items:
            if len(self.quiz_items) < 3:
                self.quiz_items.append(quiz_item)
            else:
                self.quiz_items.insert(2, quiz_item)
            self.quiz_items.insert(0, quiz_item)
        elif self.quiz_items[-1] is not quiz_item:
            self.quiz_items.insert(0, quiz_item)

    def shuffle(self):
        random.shuffle(self.quiz_items)

    @property
    def size(self):
        return len(self.quiz_items)

    @property
    def correct_answers(self):
        return sum(q.correct_answer_count > 0 and q.wrong_answer_count == 0 for q in self.all_quiz_items)

    @property
    def wrong_answers(self):
        return sum(q.wrong_answer_count > 0 for q in self.all_quiz_items)

    @property
    def practiced_question_count(self):
        return sum(q.correct_answer_count > 0 or q.wrong_answer_count > 0  for q in self.all_quiz_items)

with open(md_filename) as f:
    txt_lines = f.readlines()

# Parse questions from file lines
questions = []

for i, line in enumerate(txt_lines):
    if not line.strip().startswith('#'):
        continue
    question = line
    answer = ''
    for answer_line in txt_lines[i+1:]:
        if len(answer) == 0 and len(answer_line.strip()) == 0:
            continue  # skip empty lines berore answer text
        if not answer_line.strip().startswith('#'):
            answer += answer_line
        else:
            break
    if len(answer.strip()) > 0:
        questions.append(QuizItem(question, answer))  # don't strip answer here to preserve indentation formatting

def format_string(str):
    t = TerminalString()
    lines = str.splitlines()
    formatted_lines = []
    for l in lines:
        if re.match(r'!\[.*?\]\(', l):
            continue
        l = re.sub(r'\*\*\b(.+?)\b\*\*', t.bold(r'\1'), l)
        match = re.match(r'(^\s*[-*]\s*)', l)
        if match is not None:
            subsequent_indent = match.group(1)
            subsequent_indent = re.sub(r'[-*]', ' ', subsequent_indent)
            new_str = textwrap.fill(
                l,
                terminal_width(),
                subsequent_indent=subsequent_indent,
                expand_tabs=True,
                tabsize=4
            )
        else:
            new_str = textwrap.fill(l, terminal_width(), expand_tabs=True, tabsize=4)
        formatted_lines.append(new_str)
    return '\n'.join(formatted_lines)

def print_question(info_line, question):
    print(info_line)
    print(format_string(question))

def print_answer(answer):
    print(format_string(answer))


class CLI(cmd.Cmd):

    def __init__(self):
        cmd.Cmd.__init__(self)
        self.prompt = '> '

    def do_hello(self, arg):
        print "hello again", arg, "!"

    def help_hello(self):
        print "syntax: hello [message]",
        print "-- prints a hello message"

    def do_quit(self, arg):
        sys.exit(1)

    def help_quit(self):
        print "syntax: quit",
        print "-- terminates the application"

    # shortcuts
    do_q = do_quit


quiz_deck = QuizItemDeck(questions)
# quiz_deck.shuffle()
quiz_item = quiz_deck.next()


while quiz_item is not None:
    clear_screen()
    info_line = f'{quiz_deck.size + 1}/{quiz_deck.original_size}'
    print_question(info_line, quiz_item.question)
    user_answer = input()
    if user_answer == 'q':
        break
    clear_screen()
    print_question(info_line, quiz_item.question)
    print()
    print_answer(quiz_item.answer)
    print()
    user_answer = input()
    if user_answer == 'q':
        break
    elif len(user_answer) > 0:  # Wrong answer
        quiz_item.wrong_answer_count += 1
        quiz_deck.return_quiz_item(quiz_item)
    else:  # Correct answer
        quiz_item.correct_answer_count += 1
    quiz_item = quiz_deck.next()

clear_screen()
print(f'Opiskelit {quiz_deck.original_size - quiz_deck.size}/{quiz_deck.original_size} kysymystä')
print(f'   * {quiz_deck.correct_answers} osasit ennestään')
print(f'   * {quiz_deck.wrong_answers} opettelit nyt')
