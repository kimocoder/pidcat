from inputs.file import FileReader
print('ae.!')

reader = FileReader('query_activation_response.log')

with reader as rr:
    while True:
        print(rr.next())

print('fim')
