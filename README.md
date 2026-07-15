We are basically using TF IDF for keyword extraction 
Step 1: Cleaning the Text: Since a user ticket may contain a lot of stop words, like "is" "am" "the" It is important that we remove them. 
Let's say the user ticket is "My outlook is not receiving emails" 
Here the stop words are "My", "is", "not" It is important that we remove them, this we are already doing using TF IDF vectorizer 

vectorizer=TfidfVectorizer(stop_words="english",ngram_range=(1,2))


Step2: Creating N Grams 

Since we have set ngram_range=(1,2) the system groups the words into pairs to preserve the context. 


Step 3: Calculating Word Importance: 
The system is then creating a master list of all the words as well as pairs across the entire database and assigns a numerical weight to each word based on two factors:
	- Term Frequency: If a word appears multiple times in a ticket, its weight goes up for that ticket 
	- Inverse Document Frequency: If a word appears in almost all the tickets then its weight goes down, since it is not unique 
	For instance the word computer appears across almost all the tickets then it is assigned a smaller weight. On the other hand rare words are assigned higher weights. For instance shared mailbox, MS Teams 
	
Step 4: Vector Transformation 
Every ticket is transformed into a fixed length list of numbers. Each position corresponds to a word from the master dictionary (words excluding the stop words)
	- If the ticket contains that word then its position gets the TF IDF weight number 
	- In case the ticket does not contain that word, then the value at that position is set to 0.0
	
Step 5: Comparing the numbers:
When a new ticket arrives, it is also turned into a list of numbers.
The cosine_similarity function then multiplies the weights of the overlapping words together. 
