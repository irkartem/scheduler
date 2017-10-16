git-%: 
	git add . 
	git commit -m "$(@:git-%=%)"
	git push origin master
