"""Source adapters. Import registry of live + stub adapters."""

from .arbeitnow import ArbeitnowSource
from .ashby import AshbySource
from .base import SourceAdapter
from .greenhouse import GreenhouseSource
from .hiringcafe import HiringCafeSource
from .jobspy_boards import JobSpyBoardsSource
from .landingjobs import LandingJobsSource
from .lever import LeverSource
from .personio import PersonioSource
from .recruitee import RecruiteeSource
from .remoteok import RemoteOKSource
from .smartrecruiters import SmartRecruitersSource
from .stubs import EURES_STUB, RELOCATE_ME_STUB, WELLFOUND_STUB
from .teamtailor import TeamtailorSource
from .weworkremotely import WeWorkRemotelySource
from .workable import WorkableSource

LIVE_SOURCES = {
    "arbeitnow": ArbeitnowSource,
    "greenhouse": GreenhouseSource,
    "ashby": AshbySource,
    "lever": LeverSource,
    "workable": WorkableSource,
    "personio": PersonioSource,
    "teamtailor": TeamtailorSource,
    "smartrecruiters": SmartRecruitersSource,
    "recruitee": RecruiteeSource,
    "landingjobs": LandingJobsSource,
    "jobspy": JobSpyBoardsSource,
    "remoteok": RemoteOKSource,
    "weworkremotely": WeWorkRemotelySource,
    "hiringcafe": HiringCafeSource,
}

STUB_SOURCES = {
    "relocate.me": RELOCATE_ME_STUB,
    "wellfound": WELLFOUND_STUB,
    "eures": EURES_STUB,
}

__all__ = [
    "SourceAdapter",
    "LIVE_SOURCES",
    "STUB_SOURCES",
    "ArbeitnowSource",
    "GreenhouseSource",
    "AshbySource",
    "LeverSource",
    "WorkableSource",
    "PersonioSource",
    "TeamtailorSource",
    "SmartRecruitersSource",
    "RecruiteeSource",
    "LandingJobsSource",
    "JobSpyBoardsSource",
    "RemoteOKSource",
    "WeWorkRemotelySource",
    "HiringCafeSource",
]
