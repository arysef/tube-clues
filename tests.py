import unittest

class Test(unittest.TestCase):
    def test_name_isolation(self):
        cpp_code = '''
                    #include <iostream>
                    #include <vector>

                    void foo() {
                        std::cout << "Hello, World!" << std::endl;
                    }

                    struct T3
                    {
                        int c = 0;
                        int GetVal()
                        {
                            return c;
                        }
                    };


                    int main() {
                        foo();
                        std::vector<int> vec;
                        T3 t;
                        t.GetVal();
                        vec.push_back(42);
                        vec.size();
                        std::cout << "Goodbye, World!" << std::endl;
                    }
                    '''
        expected_names = set(["main", "size", "push_back", "GetVal", "foo"])
        isolated_names = cpp_parser.isolate_function_names(cpp_code)

        for name in expected_names:
            self.assertIn(name, isolated_names)
        for name in isolated_names:
            self.assertIn(name, expected_names)
    
    def test_tokenizer(self):
        sample_sentence = "You are an assistant who duty is to write efficient Python code."
        expected_token_count = 13
        token_count = api_usage.get_token_counts(sample_sentence)
        self.assertEqual(token_count, expected_token_count)


    def test_filter_strings(self):
        sample_strings = ["One", "Two", "Three", "Four, five, six"]
        expected_strings = ["One", "Two", "Three"]
        filtered_strings = api_usage.filter_strs(sample_strings, 3)
        self.assertEqual(filtered_strings, expected_strings)
    
    # def test_empty_list(self):
    #     self.assertEqual(split_strings([]), [])

    # def test_single_string(self):
    #     self.assertEqual(split_strings(["Hello"], 10), [["Hello"]])

    # def test_single_long_string(self):
    #     self.assertEqual(split_strings(["Hello, world!"], 5), [["Hello"], [", wor"], ["ld!"]])

    # def test_multiple_short_strings(self):
    #     self.assertEqual(split_strings(["One", "Two", "Three"], 10), [["One", "Two"], ["Three"]])

    # def test_multiple_mixed_strings(self):
    #     self.assertEqual(split_strings(["One", "Two", "Three", "Four, five, six"], 7), [['One', 'Two'], ['Three'], ['Four, f'], ['ive, si'], ['x']])

    # def test_line_breaks(self):
    #     self.assertEqual(split_strings(["One\nTwo\nThree\nFour"], 6), [['One\nTw'], ['o\nThre'], ['e\nFour']])


if __name__ == '__main__':
    unittest.main()