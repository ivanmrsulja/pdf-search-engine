#!/usr/bin/python
# vim: set fileencoding= utf-8

from graph import Graph
import pdftotext
import random
import re
import os
import sys
from termcolor import colored
from spellchecker import SpellChecker


class StackError(Exception):
    """
    Klasa modeluje izuzetke vezane za klasu Stack.
    """
    pass


class Stack(object):
    def __init__(self):
        self._data = []

    def __len__(self):
        return len(self._data)

    def is_empty(self):
        if len(self._data) == 0:
            return True
        else:
            return False

    def push(self, element):
        self._data.append(element)

    def top(self):
        return self._data[-1]

    def pop(self):
        if self.is_empty():
            raise StackError("Stack is empty.")
        return self._data.pop()


class TrieNode(object):
    """
    Moj trie node, nije mnogo, ali je posteno.
    """

    def __init__(self, char: str):
        self.char = char
        self.children = []
        self.end_of_word = False
        self.counter = 1  # koliko ima rijeci koje sadrze ovo slovo
        self.all_indexes = []
        self.indexes = set()


class Engine(object):

    def __init__(self, content, gap):
        self.root = TrieNode('*')  # moze biti bilo sta, ne ulazi u pretragu.
        self.content = content
        self.gap = gap
        self.references = set()
        self.spell = SpellChecker()

        for page in self.content["pages"]:
            self.check_references(page["content"], page["page_number"])
            tokens = page["content"].split(" ")
            for token in tokens:
                self.add_to_trie(token.lower(), page["index"])

        self.graph = graph_from_edgelist(self.references, True)
        self.vertices = self.graph._vertices  # izvinjavam se prvenstveno sebi zbog ovoga

        # glavna petlja
        while True:
            input_phrase = input(">> ")

            self.search_input = input_phrase.strip()

            if self.search_input == "":
                continue
            elif self.search_input == "/clear":
                os.system("clear")
                continue

            self.parse_and_search(self.search_input)

    def check_references(self, page, page_number):
        first = re.findall("page \d+", page)
        second = re.findall("pages \d+ and \d+", page)
        if len(first) != 0:
            for string in first:
                reference = int(string.replace("page ", ""))
                self.references.add((page_number, reference))
        if len(second) != 0:
            for string in second:
                to_split = string.replace("pages ", "")
                references = to_split.split(" and ")
                for ref in references:
                    self.references.add((page_number, int(ref)))

    def parse_and_search(self, search_input):
        if '"' in search_input:
            self.search_long_expression(search_input)
        elif "AND" in search_input or "OR" in search_input or "NOT" in search_input:
            self.search_logic_expression(search_input)
        else:
            tokens = search_input.split(" ")
            if len(tokens) == 1:
                results, set = self.search_single_word(search_input.lower())
                self.output(results)
            else:
                results, set = self.search_multiple_words(tokens)
                self.output(results)

    def inspect_phrase(self):
        if " " in self.search_input:
            correction = self.inspect_multiple_words(self.search_input.split(" "))
        else:
            correction = self.inspect_single_word(self.search_input.lower())
        print(colored("Did you mean: ", "green"), correction)

    def inspect_multiple_words(self, tokens):
        suggestion = ""
        for token in tokens:
            candidate = self.inspect_single_word(token.lower())
            if candidate == "unfortunately, there are no suggestions for this word.":
                continue
            else:
                suggestion = suggestion + candidate + " "
        return suggestion

    def inspect_single_word(self, word):
        candidates = self.spell.candidates(word)
        for candidate in candidates:
            found, node = self.find_prefix(candidate)
            if found:
                return candidate
        return "unfortunately, there are no suggestions for this word."

    def output(self, results):
        if len(results) == 0:
            print("No results have been found for this search..")
            self.inspect_phrase()
            return
        if '"' in self.search_input:
            words = []
            words.append(self.search_input.replace('"', ''))
        else:
            upper = self.search_input.replace(" AND", "").replace(" OR", "").replace(" NOT", "").replace(" )",
                                                                                                         "").replace(
                " (", "").lower().title().split(" ")
            lower = self.search_input.replace(" AND", "").replace(" OR", "").replace(" NOT", "").replace(" )",
                                                                                                         "").replace(
                " (", "").lower().split(" ")
            words = upper + lower
        separators = []
        flag = 0
        print("Search results:")
        if self.search_input == "Recursion":
            print(colored("Did you mean: ", "green"), "recursion")
        ordinal = 1
        for pair in results:
            page_num = pair[0] - self.gap
            print(colored("\n{0:2} . on index:{1:5} on page:{2:5} \n".format(ordinal, pair[0], page_num), "cyan"))
            lines = content['pages'][pair[0]]["content"].split("\n")
            for row in lines:
                line = row.replace("\n", "")
                for word in words:
                    if word in line:
                        flag = 1
                        separators.append(word)
                if flag == 1:
                    output_line = ""
                    for sep in separators:
                        tokens = line.split(sep)
                        for i in range(len(tokens)):
                            if i == len(tokens) - 1:
                                output_line = output_line + tokens[i]
                            else:
                                output_line = output_line + tokens[i] + colored(sep, "yellow")
                        line = output_line
                        output_line = ""
                    separators.clear()
                    print(line)
                    flag = 0
                else:
                    print(line)
            if ordinal % 10 == 0:
                while True:
                    choice = input("Do you want more results?[Y/n]: ")
                    if choice == "Y" or choice == "y":
                        break
                    elif choice == "N" or choice == "n":
                        return
            ordinal += 1

    def search_multiple_words(self, tokens):
        for token in tokens:
            results, intersection = self.search_single_word(token.lower())
            self.skip = token
            if len(results) != 0:
                break
        for token in tokens:
            if token == self.skip:
                continue
            new_results, indexes = self.search_single_word(token.lower())
            results = self.refresh_results(results, new_results)
            intersection = intersection & indexes

        results.sort(key=self.value_sort_key, reverse=True)

        return results, intersection

    def refresh_results(self, old, new):
        for_ret = []
        copy = True
        for pair in old:
            flag = 0
            index = pair[0]
            for new_pair in new:
                if index == new_pair[0]:
                    flag = 1
                    for_ret.append((index, pair[1] + new_pair[1] + 50))
                elif copy:
                    for_ret.append(new_pair)
            if flag == 0:
                for_ret.append((index, pair[1]))
            copy = False
        return for_ret

    def search_single_word(self, search):
        """
        Vraca sve indekse pojavljivanja reci sa brojem pojavljivanja na svakom i skup indeksa.

        :param word:  string
        :return: Tuple(indeks, broj pojavljivanja), set(indeksi)
        """
        word = search.lower()
        found, node = self.find_prefix(word)
        if found:
            indexes = node.indexes
            all_indexes = node.all_indexes
            index_with_rating = []
            for index in indexes:
                increment = 0
                try:
                    vertex = self.vertices[self.content["pages"][index]["page_number"]]
                    increment = self.graph.degree(vertex, False) * 10
                    in_degree = self.graph.incident_edges(vertex, False)
                    for edge in in_degree:
                        increment = increment + self.content["pages"][edge.out_of - self.gap].count(word)
                except:
                    pass
                index_with_rating.append((index, all_indexes.count(index) + increment))
            index_with_rating.sort(key=self.value_sort_key, reverse=True)
            return index_with_rating, indexes
        else:
            return [], set()

    def search_logic_expression(self, expression):
        e = expression.replace(" AND", "")
        ex = e.replace(" OR", "")
        exp = ex.replace(" NOT", "")
        to_calculate = self.make_post_fix_notation(expression)
        print(to_calculate)
        self.calculate_post_fix_notation(to_calculate)

    def search_long_expression(self, expression):
        results_final = []
        stripped = expression.replace('"', '')
        tokens = stripped.split(" ")
        results, intersection = self.search_multiple_words(tokens)
        for page in intersection:
            increment = 0
            try:
                vertex = self.vertices[page - self.gap]
                increment = self.graph.degree(vertex, False)
            except:
                pass
            content = self.content["pages"][page]["content"].replace("\n", " ")
            count = content.replace(" ", "").count(stripped.replace(" ", ""))
            if count == 0:
                continue
            results_final.append((page, count + increment))
        results_final.sort(key=self.value_sort_key, reverse=True)
        self.output(results_final)

    def value_sort_key(self, t):
        return t[1]

    def add_to_trie(self, text, page_index):
        """
        Dodaje rijec u trie
        """
        node = self.root  # trenutni cvor
        for char in text:
            found_in_child = False
            for child in node.children:
                if child.char == char:
                    child.counter += 1
                    node.all_indexes.append(page_index)
                    node.indexes.add(page_index)
                    node = child
                    found_in_child = True
                    break
            if not found_in_child:  # dodaje se to slovo jer ga nema
                new_node = TrieNode(char)
                node.children.append(new_node)
                node = new_node  # idemo dalje na sledece slovo
        node.end_of_word = True
        node.all_indexes.append(page_index)
        node.indexes.add(page_index)

    def find_prefix(self, prefix: str):
        """
        Vraca: Tuple[bool, object]

        Provjeri i vrati:
          Da li postoji data rijec ili prefiks u trie strukturi,
           vraca boolean i objekat zadnjeg karaktera kao TrieNode objekat
        """
        node = self.root
        if len(self.root.children) == 0:
            return False, 0
        for char in prefix:
            char_not_found = True
            for child in node.children:
                if child.char == char:
                    char_not_found = False
                    node = child
                    break
            if char_not_found:
                return False, 0
        return True, node

    def make_post_fix_notation(self, expression):
        priority = {
            "AND": 2,
            "NOT": 1,
            "OR": 1,
            "(": 0
        }
        result = ""
        tokens = expression.split(" ")
        s1 = Stack()
        for char in tokens:
            if char not in priority.keys() and char != ")":
                result = result + char + " "

            elif s1.is_empty():
                s1.push(char)
            elif char == ")":
                while True:
                    if s1.top() == "(":
                        s1.pop()
                        break
                    result = result + s1.pop() + " "
            elif priority[char] <= priority[s1.top()] and char != "(":
                result = result + s1.pop() + " "
                s1.push(char)
            else:
                s1.push(char)

        for i in range(len(s1)):
            result = result + s1.pop() + " "
        return result

    def calculate_post_fix_notation(self, expression):
        final_results = []
        trimmed = expression.strip()
        stek = Stack()
        stacked_results = Stack()
        tokens = trimmed.split(" ")
        operations = ["OR", "AND", "NOT"]
        for char in tokens:
            if char not in operations:
                result, intersection = self.search_single_word(char)
                stek.push(intersection)
                stacked_results.push(result)
            elif char == "AND":
                other = stek.pop()
                stek.push(self.intersection(stek.pop(), other))
            elif char == "OR":
                other = stek.pop()
                stek.push(self.unification(stek.pop(), other))
            elif char == "NOT":
                other = stek.pop()
                stek.push(self.difference(stek.pop(), other))
        final_intersection = stek.pop()
        for i in range(len(stacked_results)):
            results = stacked_results.pop()
            for result in results:
                if result[0] in final_intersection:
                    if len(final_results) == 0:
                        final_results.append(result)
                    for pair in final_results:
                        if pair[0] == result[0]:
                            final_results.remove(pair)
                            final_results.append((pair[0], pair[1] + result[1]))
                            break
                    else:
                        final_results.append(result)
        final_results.sort(key=self.value_sort_key, reverse=True)
        self.output(final_results)

    def intersection(self, set1, set2):
        ret = set1 & set2
        return ret

    def unification(self, set1, set2):
        ret = set1.union(set2)
        return ret

    def difference(self, set1, set2):
        ret = set1 - set2
        return ret


def get_pdf_content(file_path):
    with open(file_path, "rb") as f:
        pdf = pdftotext.PDF(f)

        result = {'pages': []}

        # iteracija kroz sve stranice
        for i, content in enumerate(pdf):
            try:
                page_number = int(content[:content.index('\n')].split()[-1])
            except:
                page_number = None

            result['pages'].append({'index': i, 'page_number': page_number, 'content': content})

    return result


def graph_from_edgelist(E, directed=False):
    """Kreira graf od ivica.

    Dozvoljeno je dva načina navođenje ivica:
          (origin,destination)
          (origin,destination,element).
    Podrazumeva se da se labele čvorova mogu hešovati.
    """
    g = Graph(directed)
    V = set()
    for e in E:
        V.add(e[0])
        V.add(e[1])

    vertices = {}  # izbegavamo ponavljanje labela između čvorova, sve su stringovi
    for v in V:
        vertices[v] = g.insert_vertex(v)  # mapa[string] = Vertex ref.

    for e in E:
        src = e[0]  # string
        dest = e[1]  # string
        element = e[2] if len(e) > 2 else None  # int ili None
        g.insert_edge(vertices[src], vertices[dest], element)  # (str, str, int/none)

    return g


if __name__ == '__main__':
    print("Opening '{}'.".format(sys.argv[1]))
    path = sys.argv[1]
    print("Loading data...")
    content = get_pdf_content(path)
    print("Data loaded successfully!")
    while True:
        i = random.randrange(0, len(content["pages"]))
        if content['pages'][i]["page_number"] is not None:
            gap = i - content['pages'][i]["page_number"]
            break
    e = Engine(content, gap)
