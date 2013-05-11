import operator
import copy
import re
import itertools

anchors_file = 'comm_out'
entities_file = 'ent_out'

anchors = {}
f = open(anchors_file, 'r', 10000)
ctr = 0
for line in f:
    anchor = line.split('\t')[0]
    if anchor not in anchors:
        anchors[anchor] = ctr
    ctr += 1

f.close()

print len(anchors)
ctr = 0
entities = {}
f = open(entities_file, 'r', 10000)

for line in f:
    entity = line.split('\t')[0]
    if entity not in entities:
        entities[entity] = ctr
    ctr += 1

f.close()
print len(entities)

for doc in range (1, 10):
    input_file = 'article' + str(doc) + '.txt'

    f = open(input_file, 'r')
    input_text = f.readlines()
    f.close()
    clean_text = str()

    for line in input_text:
            clean_text += line.rstrip('\n')
    anum = lambda x: re.sub(r'([^\s\w]|_)+', '', x.lower())
    anum_text = anum(clean_text) #return only alpha numeric + spaces
    words = anum_text.split(' ')
    grams_arr = [zip(words), zip(words, words[1:]), zip(words, words[1:], words[2:]), \
             zip(words,words[1:],words[2:],words[3:]), \
             zip(words,words[1:],words[2:],words[3:],words[4:])]

    anchors_in_doc = {}

    for grams in grams_arr:
        for gram in grams:
            new_gram = gram[0]
            for i in range(1, len(gram)):
                new_gram += ' ' + gram[i]
            if new_gram in anchors:
                if new_gram not in anchors_in_doc:
                    anchors_in_doc[new_gram] = {}

    print len(anchors_in_doc)

    anchors_in_doc_lp = {}

    entities_in_doc = {}
    anchor_index = []
           
    for key in anchors_in_doc:
        anchor_index.append(anchors[key])

    anchor_index = sorted(anchor_index, reverse = True)
    print "No. of ANCHORS", len(anchor_index)

    next_anchorindex = anchor_index.pop()
    anch_found = 0
    with open(anchors_file) as f:
        linenum = 0
        for line in f:        
            if linenum == next_anchorindex:
                anch_found += 1
                line_text = line.split('\t')
                if line_text[len(line_text)-1] == '\n':
                    line_text.remove('\n')
                anchors_in_doc_lp[line_text[0]] = int(line_text[1])/(1.0*int(line_text[2]))
                for i in range (3, len(line_text), 2):
                    if line_text[i] not in anchors_in_doc[line_text[0]]:
                        anchors_in_doc[line_text[0]][line_text[i]] = int(line_text[i+1])/(1.0*int(line_text[1]))
                    if line_text[i] not in entities_in_doc:
                        if line_text[i] in entities:
                            entities_in_doc[line_text[i]] = set()
                if not anchor_index: break
                next_anchorindex = anchor_index.pop()
            linenum += 1
    print "ANCHORS FOUND", anch_found

    entity_index = []
    not_found_ent = 0
    for key1 in entities_in_doc:
        if key1 in entities:
            entity_index.append(entities[key1])
        else:
            not_found_ent += 1
            
    entity_index = sorted(entity_index, reverse = True)
    print len(entity_index)
    print "NOT FOUND ENTITIES", not_found_ent

    ent_found = 0
    next_entityindex = entity_index.pop()
    with open(entities_file) as f:
        linenum = 0
        for line in f:
            if linenum == next_entityindex:
                ent_found += 1
                line_text = line.split('\t')
                if line_text[len(line_text)-1] == '\n':
                    line_text.remove('\n')
                for i in range (1, len(line_text)):
                    entities_in_doc[line_text[0]].add(line_text[i])
                if not entity_index: break
                next_entityindex = entity_index.pop()
            linenum += 1
    print ent_found

    unambig = {}
    ambig = {}

    for key1 in anchors_in_doc:
        if len(anchors_in_doc[key1]) == 1:
            if key1 not in unambig:
                unambig[key1] = copy.deepcopy(anchors_in_doc[key1])
        else:
            if key not in ambig:
                ambig[key1] = copy.deepcopy(anchors_in_doc[key1])

    print len(ambig)
    print len(unambig)

    avg_sim = {}
    for key1 in unambig:
        for ent1 in unambig[key1]:
            avg_sim[ent1] = 0
            for key2 in unambig:
                for ent2 in unambig[key2]:
                    if ent1 != ent2:
                        if (ent1 in entities) & (ent2 in entities):
                            inter = len((entities_in_doc[ent1]).intersection(entities_in_doc[ent2]))
                            uni = len((entities_in_doc[ent1]).union(entities_in_doc[ent2]))
                            sim = inter/(1.0*uni)
                            avg_sim[ent1] += sim
        avg_sim[ent1] = avg_sim[ent1]/(1.0*(len(unambig)-1))

    for key1 in ambig:
        for ent1 in ambig[key1]:
            ambig[key1][ent1] = 0
            for key2 in unambig:
                for ent2 in unambig[key2]:
                    if (ent1 in entities) & (ent2 in entities):
                        inter = len((entities_in_doc[ent1]).intersection(entities_in_doc[ent2]))
                        uni = len((entities_in_doc[ent1]).union(entities_in_doc[ent2]))
                        sim = inter/(1.0*uni)
                        ambig[key1][ent1] += anchors_in_doc_lp[key2]*avg_sim[ent2]*sim

    f = open('op/output' + str(doc), 'w', 10000)

    disambiguated = {}
    for anch in ambig:
            if anchors_in_doc_lp[anch] > 0:
                    disambiguated[anch] = {}
                    for ent in ambig[anch]:
                            disambiguated[anch][ent] = anchors_in_doc[anch][ent]*ambig[anch][ent]
                    max_disamb = max(disambiguated[anch].iteritems(), key=operator.itemgetter(1))
                    f.write(str(anch) + '\t' + str(anchors_in_doc_lp[anch]) + '\t' + str(max_disamb[0]) + '\t' + str(anchors_in_doc[anch][max_disamb[0]]) + '\t' + str(ambig[anch][max_disamb[0]])+ '\n')

    for anch in unambig:
        if anchors_in_doc_lp[anch] > 0.05:
            for ent in unambig[anch]:
                f.write(str(anch) + '\t' + str(anchors_in_doc_lp[anch]) + '\t' + str(ent) + '\t' + str(anchors_in_doc[anch][ent]) + '\t' + str(0) + '\n')
    f.close()
