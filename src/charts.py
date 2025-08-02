'''
great
'''
import os
from sqlalchemy import Column, Integer, String
from . import db
from . import utils
#from sqlalchemy.exc import NoResultFound
#from sqlalchemy.orm import relationship

class Chart(db.Base):
    '''
    represents a chart.
    requires an accompanying .zip
    '''
    __tablename__ = "charts"
    id = Column(Integer, primary_key=True, autoincrement=True)
    song_title = Column(String)
    #difficulties = relationship("ChartDiff", back_populates="chart")
    zip_path = Column(String)

    def to_dict(self):
        '''
        turns this object into a dictionary.
        used for JSON responces
        '''
        return {
            "id": self.id,
            "song_title": self.song_title,
            "zip_path": self.zip_path,
        }

# not used
#class ChartDiff(db.Base):
#    __tablename__ = "diffs"
#    id = Column(Integer, primary_key=True, autoincrement=True)
#    name = Column(String)
#    chart_id = Column(Integer, ForeignKey("charts.id"))
#    chart = relationship("Chart", back_populates="difficulties")

def upload_chart_zip(in_file, data_directory):
    '''
    handles uploading a chart
    '''
    uid = utils.unique()
    mediapath = os.path.join(data_directory, uid)
    utils.raise_to_validate_path(mediapath)

    with open(mediapath, mode="wb") as f:
        data = in_file.read()
        f.write(data)
