#include <unistd.h>
#include <stdio.h>

int main()
{
	int i;
	for(i=0;i<20;i++){
		sleep(1);
		printf("looping #%d\n",i);
	}
	return 0;
}
