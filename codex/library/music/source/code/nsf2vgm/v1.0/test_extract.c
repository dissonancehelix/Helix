#include <stdio.h>
#include <string.h>

void extract_folder_name(const char *m3u_path, char *folder_name, size_t folder_name_size);

int main() {
    char folder[512];
    const char *test = "./Kirby's Adventure Hoshi no Kirby - Yume no Izumi no Monogatari (1993-03-23)(HAL Laboratory)(Nintendo).m3u";
    extract_folder_name(test, folder, sizeof(folder));
    printf("Input: %s\n", test);
    printf("Output: %s\n", folder);
    return 0;
}
