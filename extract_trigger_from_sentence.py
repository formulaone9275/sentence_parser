from __future__ import unicode_literals, print_function
from lxml import etree
import operator as op
#import of nlputils
import codecs
import sys
import os
#sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
#from protolib.python import document_pb2, rpc_pb2
#from utils.rpc import grpcapi
import pickle

def process_one_document(request):
    # Use biotm2 as server.
    interface = grpcapi.GrpcInterface(host='128.4.20.169')
    # interface = grpcapi.GrpcInterface(host='localhost')
    response = interface.process_document(request)
    assert len(response.document) == 1
    return response.document[0]


def parse_using_bllip(doc):
    request = rpc_pb2.Request()
    request.request_type = rpc_pb2.Request.PARSE_BLLIP
    request.document.extend([doc])
    return process_one_document(request)


def parse_using_stanford(doc):
    request = rpc_pb2.Request()
    request.request_type = rpc_pb2.Request.PARSE_STANFORD
    request.document.extend([doc])
    return process_one_document(request)


def split_using_stanford(doc):
    request = rpc_pb2.Request()
    request.request_type = rpc_pb2.Request.SPLIT
    request.document.extend([doc])
    return process_one_document(request)


def run(text):

    raw_doc = document_pb2.Document()
    raw_doc.doc_id = '26815768'
    raw_doc.text = text

    # Parse using Bllip parser.
    result = parse_using_bllip(raw_doc)
    #print(result)
    return result
    # Parse Using Stanford CoreNLP parser.
    #result = parse_using_stanford(raw_doc)
    #print(result)

    # Only split sentences using Stanford CoreNLP.
    #for i in range(100):
    #    result = split_using_stanford(raw_doc)
    #    print('Split {} documents'.format(i))
def extract_trigger(inputfile,picklefile):
    file_dic={}
    with codecs.open(inputfile, encoding='utf8') as f:
        for line in f:
            line = line.strip()
            info, tagged = line.split('\t')
            features = info.split(' ')
            interaction_relation=True if features[0]=='R_PPI' else False
            tagged=tagged.replace('<0>','')
            tagged=tagged.replace('</0>','')
            tagged=tagged.replace('<1>','<Gene>')
            tagged=tagged.replace('</1>','</Gene>')
            removed_tag=tagged.replace('<Gene>','')
            removed_tag=removed_tag.replace('</Gene>','')
            if interaction_relation is True:
                #parse the sentence here
                parse_result=run(removed_tag)

                #build a dictionary to store the incoming dependency
                incoming_dependency={}
                trigger_dependency={}
                for sente in parse_result.sentence:
                    for dep in sente.dependency:
                        g_index=getattr(dep,'gov_index')
                        if g_index not in incoming_dependency.keys():
                            incoming_dependency[g_index]=[dep.relation]
                        else:
                            incoming_dependency[g_index].append(dep.relation)
                for di in incoming_dependency.keys():
                    if len(incoming_dependency[di])>=2:
                        trigger_dependency[di]=(parse_result.token[di].word,incoming_dependency[di])
                if tagged not in file_dic.keys():
                    file_dic[tagged]=trigger_dependency
                else:
                    if file_dic[tagged]!=trigger_dependency:
                        print('Error!')
    with open(picklefile, 'wb') as f:

        pickle.dump(file_dic, f, pickle.HIGHEST_PROTOCOL)

def read_pickle(picklefile):
    delete_list=['compound','det']
    with open(picklefile, 'rb') as f:
        data = pickle.load(f,encoding="latin1")
        #print(data)
        new_dic={}
        #delete the dependenct 'compound'
        for di in data.keys():
            sub_dic={}
            for ddi in data[di].keys():
                dependency_list=data[di][ddi][1]
                dependency_list=list(set(dependency_list))
                for deli in delete_list:
                    if deli in dependency_list:
                        dependency_list.remove(deli)
                if len(dependency_list)>=2:
                    sub_dic[ddi]=(data[di][ddi][0],dependency_list)
            if len(sub_dic)>0:
                new_dic[di]=sub_dic
    #print out the new dictionary
    for di in new_dic.keys():
        print(di)
        for ddi in new_dic[di].keys():
            print(ddi)
            print(new_dic[di][ddi][0])
            print(new_dic[di][ddi][1])


if __name__ == '__main__':
    inputfile='aimed_gang.txt'
    picklefile='trigger_dependency.pickle'
    #extract_trigger(inputfile,picklefile)
    read_pickle(picklefile)