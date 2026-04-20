celery -A workers.evaluation_tasks worker -Q evaluation_queue --concurrency=1 --loglevel=info
 // for runnign evaluation worker
celery -A workers.plagiarism_tasks worker -Q plagiarism_queue --concurrency=1 --loglevel=info
 // for running plagiarism worker
celery -A workers.question_tasks worker -Q question_queue --concurrency=1 --loglevel=info
 // for running question worker
ssh -L 11434:localhost:11434 rishabh.jain23b@172.16.2.17
 // Use this command to run ollama from college gpu server to http://localhost:11434
~/bin/ollama serve > ollama.log 2>&1 & 
// to run ollama server in background on ssh server
ps -fu $USER 
// can see all the processes by the specific user in terminal
