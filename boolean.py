import re
from nltk import word_tokenize
from nltk.stem import PorterStemmer
from collections import OrderedDict
from itertools import chain
import tkinter as tk
from tkinter import *
from PIL import ImageTk, Image
import os
import requests
import json

stemmer = PorterStemmer()


class BooleanRetrieval:
    def __init__(self):
        self.index = {}        # declaring inverted index
        self.dictionary = {}         # declaring positional index
        fptr = open("Stopword-List.txt")      # reading stop word from file
        self.stopwords_list = fptr.readlines()
        self.stopwords_list = [x.rstrip() for x in self.stopwords_list]
        fptr.close()

    def tokenization(self, docId):
        # This func will open the coc file and return the tokens
        fptr = open("Abstracts/" + str(docId) + ".txt")
        files = fptr.read().lower()                     # lower_casing the words
        files = re.sub('[^A-Za-z]+', ' ', files)        # word only contain alphabet
        tokens = word_tokenize(files)
        tokens = list(set(tokens))  # removing duplicates
        fptr.close()
        return tokens

    def inverted_index(self):
        for i in range(1, 449):
            tokens = self.tokenization(i)  # calling tokenization func which return list of tokens
            for term in tokens:
                if term not in self.stopwords_list:
                    term = stemmer.stem(term)      # removing stopwords
                    if len(term) > 1:              # length of token should be greater than 1
                        if term in self.index:      # term already exist
                            self.index[term].append(i)             # append document id
                            self.index[term] = list(set(self.index[term]))
                            self.index[term].sort()
                        else:                        # term not exist
                            self.index[term] = [i]
        index = OrderedDict(sorted(self.index.items())) # sorting dictionary
        with open("InvertedIndex.txt", 'w') as f:
            for key, value in index.items():
                f.write('%s-->%s\n' % (key, value))

    def posting(self, term, flag):
        if flag == 1:
            if term in self.index:       # getting posting list from inverted index
                po = self.index[term]
                return po
            else:
                return None
        else:                           # getting posting list from positional index
            if term in self.dictionary:
                po = self.dictionary[term]
                return po
            else:
                return None

    def inverted_query(self, query):      # Function for boolean query
        self.inverted_index()               # initializing inverted index
        result = []
        query = re.sub('[^A-Za-z]+', ' ', query)  # applying regex to query
        query = query.lower()
        query = word_tokenize(query)              # generate tokens of query
        for t in range(0, len(query)):
            if query[t] != 'and' and query[t] != 'or' and query[t] != 'not':
                query[t] = stemmer.stem(query[t])      # applying porter stemming to query

        if len(query) == 2:        # if length of query is 2
            if query[0] == 'not':    # if it is not query
                op = self.posting(query[1],1)
                if op is not None and result is not None:
                    result = list(set(result) - set(op))   # performing not operation
        elif len(query) == 1:
            result = self.posting(query[0], 1)    # if length is 1 just return the posting list of term
        else:                                     # if length is > 2
            result = self.posting(query[0], 1)
            for t in range(1, len(query)):
                if query[t] == 'and':      # if operator is and
                    if query[t + 1] != 'not':    # check the next term if it is other than 'not'
                        op = self.posting(query[t + 1], 1)        # get posting of next term of And operator
                        if op is not None and result is not None:
                            result = list(set(op) & set(result))    # perform intersection
                    else:
                        op = self.posting(query[t + 2], 1)        # if next term is not than get posting of next term
                        if op is not None and result is not None:
                            temp = list(set(result) - set(op))     # perform not operation
                            result = list(set(op) & set(result))     # perform intersection of first and result of not operation

                if query[t] == 'or':                                # if operator is 'or'
                    if query[t + 1] != 'not':                      # this will work same as and operation
                        op = self.posting(query[t + 1], 1)
                        if op is not None and result is not None:
                            result = list(set(chain(op, result)))    # taking union of two list

                    else:
                        op = self.posting(query[t + 2], 1)
                        if op is not None and result is not None:
                            temp = list(set(result) - set(op))
                            result = list(set(chain(temp, result)))
        return sorted(result)            # return sorted output

    def positional_index(self):             # Creating Positional index
        for i in range(1, 449):
            fptr = open("Abstracts/" + str(i) + ".txt")         # Reading files
            files = fptr.read().lower()            # lowercase
            files = re.sub('[^A-Za-z0-9]+', ' ', files)     # removing all special characters
            tokens = word_tokenize(files)              # generating tokens
            position = 1                             # initializing the position to 1 at the start of each file
            for term in tokens:
                posting = []                   # declaring temporary list which contains the position
                if len(term) > 1:              # length of tokens should be greater than 1
                    if term.isalpha():           # checking the tokens only contains alphabet (Assuming only alphabets query)
                        if term not in self.stopwords_list:  # if not a stopword
                            term = stemmer.stem(term)           # apply porter stemming
                            if term not in self.dictionary:     # if not in dictionary

                                posting.append(position)        # insert position in list
                                self.dictionary[term] = {}      # intialize dictionary
                                self.dictionary[term][i] = posting     # at doc id key value is the list of positions
                                position = position + 1
                            else:
                                if i not in self.dictionary[term].keys():      # if doc is not in dict
                                    posting.append(position)                    # append position to list
                                    self.dictionary[term][i] = posting         #  insert list to dictionary at doc id key

                                else:                                           # if term and doc already exist
                                    self.dictionary[term][i].append(position)   # simply append the position on list
                                    self.dictionary[term][i].sort()             # sort the position
                                position = position + 1
                        else:
                            position = position + 1
                    else:
                        position = position + 1
                else:
                    position = position + 1
        fptr = open("positional.txt", "w")            # write the positional index on file
        for key in sorted(self.dictionary):
            fptr.write(key+"==>"+str(self.dictionary[key])+"\n")
        fptr.close

    def proximity_query(self, query):    # Function for proximity query
        self.positional_index()             # initialize positional index
        result = []
        list1 = {}                        # dict for term 1
        list2 = {}                        # dict for term 2
        query = query.lower()              # convert query in lower case
        query = word_tokenize(query)        # generate tokens of query
        for t in range(0, len(query)):
            query[t] = stemmer.stem(query[t])       # apply porter stemming on query
        for i in range(0, len(query)):
            if '/' in query[i]:              # if term contain / then remove it and store the remaining number to dist
                dist = int(re.sub('[^0-9]+', ' ', query[i]))
                list2 = self.posting(query[i-1], 2)         # get posting of term 2
                list1 = self.posting(query[i-2], 2)         # get posting of term 1
                list1 = dict([(key, val) for key, val in list1.items() if key in list2])  # to remove uncommon documents
                list2 = dict([(key, val) for key, val in list2.items() if key in list1])  # From StackOverflow
                for t in list1:
                    for k in range(0, len(list1[t])):
                        for j in range(0, len(list2[t])):
                            if abs(list1[t][k] - list2[t][j]) <= dist + 1:  # if distance between term is equal to dist
                                result.append(t)            # append doc id in the result list
        return set(result)     # return the result set containing all doc

def Search():
    br = BooleanRetrieval()                             # initialize object of boolean retrieval class
    query = str(query_text.get("1.0", END))             # store query from the search box
    if '/' not in query:
        result = br.inverted_query(query)       # if it is simple query
    else:
        result = br.proximity_query(query)     # if it is proximity query

    output.insert(END, 'The Retrieved Documents are ==>  ' + str(result) + ' \n')   # displaying result set


root = tk.Tk()              # onward code is for GUI
root.title('Boolean Query Search Engine')
root.geometry('700x400')
root.configure(bg='grey')
img = ImageTk.PhotoImage(Image.open(requests.get("https://tse2.mm.bing.net/th?id=OIP.VECMkp3p665hSrZTgm6r3AHaD7&pid=Api&P=0&w=325&h=172", stream=True).raw))
panel = Label(root, image=img)   # inserting image
panel.pack()

query_text = Text(root, height=2, width=82)     # Search box
query_text.insert(END, 'Enter your Query.........')
query_text.pack()

search_button = Button(root, height=2, width=15,bg="black", fg="white" , text="Search", command=Search)
search_button.pack()                # button

output = Text(root, height=5,
              width=82,
              bg="light yellow")            # output text
output.pack()

root.mainloop()
