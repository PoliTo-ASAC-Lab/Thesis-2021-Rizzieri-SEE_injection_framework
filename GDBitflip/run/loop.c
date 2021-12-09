#include <stdio.h>
#include <unistd.h>

int main()
{	
	int i=0;
	while(i++<10){
		sleep(10);
		printf("ciao\n");
	}
}
