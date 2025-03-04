'''
FCC sample database models
'''

import datetime
from typing import Optional
from sqlmodel import Field, Relationship, SQLModel
from sqlmodel import Column, String, Float, Integer, DateTime


class Stack(SQLModel, table=True):
    '''
    Class describing stacks table in the database.
    '''
    id: int | None = Field(default=None, primary_key=True)
    name: str
    path: str

    samples: list['Sample'] = Relationship(back_populates='stack')


class ProducerSampleLink(SQLModel, table=True):
    '''
    Class describing the link between sample producer and sample.
    '''
    sample_id: int | None = Field(default=None,
                                  foreign_key='sample.id',
                                  primary_key=True)
    producer_id: int | None = Field(default=None,
                                    foreign_key='producer.id',
                                    primary_key=True)


class Producer(SQLModel, table=True):
    '''
    Class describing the sample producers table in the database.
    '''
    id: int | None = Field(default=None, primary_key=True)
    username: str
    name: Optional[str] = None

    samples: list['Sample'] = Relationship(back_populates='producers',
                                           link_model=ProducerSampleLink)


class Sample(SQLModel, table=True):
    '''
    Class describing sample table in the database.
    '''
    id: Optional[int] = Field(default=None, primary_key=True)
    # Sample category
    accelerator: str
    event_type: str = Field(sa_column=Column('event-type', String))
    file_type: Optional[str] = Field(sa_column=Column('file-type', String,
                                                      default=None))
    campaign: Optional[str] = None
    detector: Optional[str] = None
    process_name: str = Field(sa_column=Column('process-name', String))

    # Sample params
    cross_section: Optional[float] = Field(sa_column=Column('cross-section',
                                                            Float,
                                                            default=None))
    n_events: Optional[int] = Field(sa_column=Column('n-events',
                                                     Integer, default=None))
    sum_of_weights: Optional[float] = Field(sa_column=Column('sum-of-weights',
                                                             Float,
                                                             default=None))
    n_files_good: Optional[int] = Field(sa_column=Column('n-files-good',
                                                         Integer,
                                                         default=None))
    n_files_bad: Optional[int] = Field(sa_column=Column('n-files-bad',
                                                        Integer,
                                                        default=None))
    n_files_eos: Optional[int] = Field(sa_column=Column('n-files-eos',
                                                        Integer,
                                                        default=None))
    size: Optional[int]
    path: Optional[str] = None
    # TODO: Number of events and sum of weights per file
    # files: Optional[str] = None
    description: Optional[str] = None
    comment: Optional[str] = None
    matching_params: Optional[str] = Field(sa_column=Column('matching-params',
                                                            String,
                                                            default=None))
    k_factor: Optional[float] = Field(sa_column=Column('k-factor', Float,
                                                       default=None))
    matching_eff: Optional[float] = Field(sa_column=Column('matching-eff',
                                                           Float,
                                                           default=None))
    status: str
    last_update: Optional[datetime.datetime] = Field(
        sa_column=Column('last-update', DateTime, default=None))

    # Relationships
    stack_id: int | None = Field(default=None, foreign_key='stack.id')
    stack: Stack | None = Relationship(back_populates='samples')

    producers: list['Producer'] = Relationship(back_populates='samples',
                                               link_model=ProducerSampleLink)
