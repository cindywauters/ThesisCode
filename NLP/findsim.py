word_vect = KeyedVectors.load_word2vec_format("SO_vectors_200.bin", binary=True)
initial_sentence = clean_text(sys.argv[1])


bestmatching = {}

while posts:
  for post in posts:
      new_text=post[1] + " " + post[2]
      new_text=clean_text(new_text)
      cossim = 0
      if(len(new_text) != 0):
        cossim = word_vect.n_similarity(initial_sentence.split(), new_text.split())
      if(len(bestmatching) <5):
        bestmatching[post[0]] = cossim
      elif(min(bestmatching.items(), key=operator.itemgetter(1))[1] < cossim):
         del bestmatching[min(bestmatching.items(), key=operator.itemgetter(1))[0]]     
         bestmatching[post[0]] = cossim
  posts = cursor_issues.fetchmany(1000)

bestmatching = sorted(bestmatching.items(), key=lambda x: x[1], reverse=True)