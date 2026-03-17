#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>

static unsigned char Read4Bit(FILE *file)
{
	char character = fgetc(file);

	if (character >= 'A')
		character = character - 'A' + 0xA;
	else
		character = character - '0' + 0;

	return character;
}

static unsigned char Read8Bit(FILE *file)
{
	unsigned char nibble1 = Read4Bit(file);
	unsigned char nibble2 = Read4Bit(file);

	return (nibble1<<4)|nibble2;
}

static unsigned short Read16Bit(FILE *file)
{
	unsigned char byte1 = Read8Bit(file);
	unsigned char byte2 = Read8Bit(file);

	return (byte1<<8)|byte2;
}

static unsigned long Read24Bit(FILE *file)
{
	unsigned char byte1 = Read8Bit(file);
	unsigned char byte2 = Read8Bit(file);
	unsigned char byte3 = Read8Bit(file);

	return (byte1<<16)|(byte2<<8)|byte3;
}

static unsigned long Read32Bit(FILE *file)
{
	unsigned short short1 = Read16Bit(file);
	unsigned short short2 = Read16Bit(file);

	return (short1<<16)|short2;
}

int main(int argc, char **argv)
{
	int exit_code = EXIT_SUCCESS;

	if (argc < 3)
	{
		fputs("Error: You must supply the input and output filenames as parameters\n", stderr);
		exit_code = EXIT_FAILURE;
	}
	else
	{
		FILE *in_file = fopen(argv[1], "r");

		if (in_file == NULL)
		{
			fprintf(stderr, "Error: Could not open file '%s'\n", argv[1]);
			exit_code = EXIT_FAILURE;
		}
		else
		{
			FILE *out_file = fopen(argv[2], "ab");

			if (out_file == NULL)
			{
				fprintf(stderr, "Error: Could not create file '%s'\n", argv[2]);
				exit_code = EXIT_FAILURE;
			}
			else
			{
				for (;;)
				{
					unsigned char record_start = fgetc(in_file);

					if (record_start != 'S')
						break;

					unsigned char record_type = fgetc(in_file);
					unsigned char byte_count = Read8Bit(in_file);
					unsigned long address;

					switch (record_type)
					{
						case '0':
							// Just do nothing
							break;

						case '1':
							address = Read16Bit(in_file);

							fseek(out_file, address, SEEK_SET);
							for (unsigned char i = 0; i < byte_count - 3; ++i)
								fputc(Read8Bit(in_file), out_file);

							break;

						case '2':
							address = Read24Bit(in_file);

							printf("%X\n", address);
							fseek(out_file, address, SEEK_SET);
							for (unsigned char i = 0; i < byte_count - 4; ++i)
								fputc(Read8Bit(in_file), out_file);

							break;

						case '3':
							address = Read32Bit(in_file);

							fseek(out_file, address, SEEK_SET);
							for (unsigned char i = 0; i < byte_count - 5; ++i)
								fputc(Read8Bit(in_file), out_file);

							break;

						case '5':
							fputs("Encountered 5\n", stderr);
							break;

						case '6':
							fputs("Encountered 6\n", stderr);
							break;

						case '7':
							fputs("Encountered 7\n", stderr);
							break;

						case '8':
							fputs("Encountered 8\n", stderr);
							break;

						case '9':
							fputs("Encountered 9\n", stderr);
							break;

						default:
							fputs("Error: Invalid record type\n", stderr);
							exit_code = EXIT_FAILURE;
							break;
					}

					while (fgetc(in_file) != '\n'); // Move onto next line
				}

				fclose(out_file);
			}

			fclose(in_file);
		}
	}

	return exit_code;
}
