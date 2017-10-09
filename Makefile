git-%: 
	git commit -m "$(@:git-%=%)"
	git push origin master
