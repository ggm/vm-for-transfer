#!/bin/bash
input=test/data/
output=test/expected_output/

echo "============================================"
echo "* Running tests..."
echo "* input = $input"
echo "* expected_output = $output"
echo "============================================"

for arg in `ls $output` ; do
  python3 src/compiler/ -i $input${arg/.v?x/.t?x} -d compiler.log > compiler.out
  if diff compiler.out $output$arg > test_results.log ; then
    echo $arg "-- OK"
  else
    echo $arg "-- Error"
    cat test_results.log
    fi
done

rm -f compiler.log compiler.out test_results.log
