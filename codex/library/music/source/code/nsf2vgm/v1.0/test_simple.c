#include <stdio.h>
#include <stdlib.h>
#include "../nezplug.h"
#include "../vgmwrite.h"

int main() {
    NEZ_PLAY* nez;
    FILE* fp;
    unsigned char* data;
    long size;
    
    printf("Creating NEZPlug instance...\n");
    nez = NEZNew();
    if (!nez) {
        printf("Failed to create NEZPlug\n");
        return 1;
    }
    printf("NEZPlug created\n");
    
    printf("Initializing VGM...\n");
    vgm_init();
    printf("VGM initialized\n");
    
    printf("Opening NSF file...\n");
    fp = fopen("test/battle_in_city.nsf", "rb");
    if (!fp) {
        printf("Failed to open file\n");
        return 1;
    }
    printf("File opened\n");
    
    fseek(fp, 0, SEEK_END);
    size = ftell(fp);
    fseek(fp, 0, SEEK_SET);
    printf("File size: %ld\n", size);
    
    data = malloc(size);
    if (!data) {
        printf("Failed to allocate memory\n");
        return 1;
    }
    printf("Memory allocated\n");
    
    fread(data, 1, size, fp);
    fclose(fp);
    printf("File read\n");
    
    printf("Loading NSF...\n");
    fflush(stdout);
    if (NEZLoad(nez, data, size) != 0) {
        printf("Failed to load NSF\n");
        return 1;
    }
    printf("NSF loaded\n");
    
    printf("Success!\n");
    return 0;
}
