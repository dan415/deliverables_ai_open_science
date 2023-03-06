import json
import os
import unittest
import sys
from deliverable1.src import pdf_analysis


class MyTestCase(unittest.TestCase):

    def check_correct_num_outputs(self, outputdir):
        return len(os.listdir(outputdir))

    def test_01_blank_pdf(self):
        outputdir = "deliverable1/test/cases/output"
        if not os.path.exists(outputdir):
            os.mkdir(outputdir, 0o777)
        try:
            pdf_analysis.main("deliverable1/test/cases/case_002", outputdir, "deliverable1/config.json")
        except Exception as ex:
            self.assertEqual(True, False, msg="Exception raised: " + str(ex))
        self.assertTrue(os.path.exists(outputdir + "/figures.png"))
        self.assertTrue(os.path.exists(outputdir + "/links.txt"))
        self.assertTrue(os.path.exists(outputdir + "/summary.json"))
        self.assertFalse(os.path.exists(outputdir + "/wordcloud.png"))

    def test_02_correct_num_papers(self):
        outputdir = "deliverable1/test/cases/output"
        if not os.path.exists(outputdir):
            os.mkdir(outputdir, 0o777)
        try:
            pdf_analysis.main("deliverable1/test/cases/case_02", outputdir, "deliverable1/config.json")
        except Exception as ex:
            self.assertEqual(True, False, msg="Exception raised: " + str(ex))
        self.assertEqual(7, self.check_correct_num_outputs(outputdir))

    def test_03_correct_num_figures(self):
        outputdir = "deliverable1/test/cases/output"
        if not os.path.exists(outputdir):
            os.mkdir(outputdir, 0o777)
        try:
            pdf_analysis.main("deliverable1/test/cases/case_03", outputdir, "deliverable1/config.json")
        except Exception as ex:
            self.assertEqual(True, False, msg="Exception raised: " + str(ex))
        with open("deliverable1/test/cases/output/summary.json", "r") as f:
            summary = json.load(f)
        total_figures = sum([summary[elem]["figures"] for elem in summary.keys()])
        self.assertEqual(total_figures, 25)

    def test_03_correct_num_links(self):
        outputdir = "deliverable1/test/cases/output"
        if not os.path.exists(outputdir):
            os.mkdir(outputdir, 0o777)
        try:
            pdf_analysis.main("deliverable1/test/cases/case_03", outputdir, "deliverable1/config.json")
        except Exception as ex:
            self.assertEqual(True, False, msg="Exception raised: " + str(ex))
        with open("deliverable1/test/cases/output/summary.json", "r") as f:
            summary = json.load(f)
        total_links = sum([len(summary[elem]["links"]) for elem in summary.keys()])
        self.assertEqual(total_links, 8)


if __name__ == '__main__':
    unittest.main()
