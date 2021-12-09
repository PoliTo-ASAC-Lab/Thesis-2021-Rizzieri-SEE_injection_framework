#include <stdio.h>
#include <unistd.h>
#include <time.h>
#include <stdlib.h>


int main(){
	srand(time(NULL));   // Initialization, should only be called once.
	int r = rand();      // Returns a pseudo-random integer between 0 and RAND_MAX.
	if (r%10 == 5){
		printf("HIT!\n");
		sleep(60);
	}
	int i=0;
	for (int i = 0; i < 100; ++i)
	{
		printf("i = %d\n",i );
	}
}


