from IPython.nbconvert.preprocessors import Preprocessor
from IPython.utils.traitlets import Unicode, Integer
from nbgrader import utils
from nbgrader.api import Gradebook

class OverwriteGradeCells(Preprocessor):
    """A preprocessor to save information about grade cells."""

    db_name = Unicode("gradebook", config=True, help="Database name")
    db_ip = Unicode("localhost", config=True, help="IP address for the database")
    db_port = Integer(27017, config=True, help="Port for the database")

    assignment_id = Unicode(u'assignment', config=True, help="Assignment ID")

    def preprocess(self, nb, resources):
        # connect to the mongo database
        self.gradebook = Gradebook(self.db_name, ip=self.db_ip, port=self.db_port)
        self.assignment = self.gradebook.find_assignment(
            assignment_id=self.assignment_id)
        self.notebook_id = resources['unique_key']

        nb, resources = super(OverwriteGradeCells, self).preprocess(nb, resources)

        return nb, resources

    def preprocess_cell(self, cell, resources, cell_index):
        if utils.is_grade(cell):
            try:
                grade_cell = self.gradebook.find_grade_cell(
                    grade_id=cell.metadata.nbgrader.grade_id,
                    notebook_id=self.notebook_id,
                    assignment=self.assignment)
            except:
                return cell, resources

            cell.metadata.nbgrader['points'] = grade_cell.max_score

            # we only want the source and checksum for non-solution cells
            if not utils.is_solution(cell) and grade_cell.source:
                old_checksum = grade_cell.checksum
                new_checksum = utils.compute_checksum(cell)

                if old_checksum != new_checksum:
                    self.log.warning("Checksum for grade cell %s has changed!", grade_cell.grade_id)

                cell.source = grade_cell.source
                cell.metadata.nbgrader['checksum'] = grade_cell.checksum

            self.log.debug("Overwrote grade cell %s", grade_cell.grade_id)

        return cell, resources
