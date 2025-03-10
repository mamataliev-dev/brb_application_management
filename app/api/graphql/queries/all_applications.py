import logging

from sqlalchemy import case, func
from graphene import ObjectType, List, String, Argument, Int, Field

from app.api.graphql.mutations.auth.auth_decorator import login_required
from app.api.graphql.types import ApplicationConnection, ApplicationFilterInput, ApplicationSortInput, SortDirection, \
    BranchCount
from app.models import Application as ApplicationModel
from app.api.graphql.utils import build_application_response
from app.extensions import db

logger = logging.getLogger(__name__)


class AllApplicationQuery(ObjectType):
    """
    GraphQL Query class for fetching all Applications.

    Attributes:
        fetch_all_application (List): A GraphQL field to retrieve all applications.
    """

    fetch_all_applications = Field(
        ApplicationConnection,
        filter=Argument(ApplicationFilterInput, description="Filter applications"),
        sort=Argument(List(ApplicationSortInput), description="Sort applications"),
        search=Argument(String, description="Search by client name or phone number"),
        first=Argument(Int, default_value=10, description="Number of applications to return"),
        offset=Argument(Int, default_value=0, description="Offset from start of result"),
    )

    fetch_deleted_applications = Field(
        ApplicationConnection,
        first=Argument(Int, default_value=10, description="Number of deleted applications to return"),
        sort=Argument(List(ApplicationSortInput), description="Sort applications"),
        offset=Argument(Int, default_value=0, description="Offset from start of result"),
        search=Argument(String, description="Search by client name or phone number"),
    )

    @classmethod
    @login_required(role=["admin", "manager"])
    def resolve_fetch_all_applications(cls, root, info, filter=None, sort=None, search=None, first=10, offset=0):
        """
        Resolves the query to fetch all Applications.

        Args:
            root (Any): GraphQL root argument (unused).
            info (ResolveInfo): GraphQL resolver context.
            filter (ApplicationFilterInput): Filters to apply.
            sort ([ApplicationSortInput]): Sort criteria.
            search (str): Search term for client name or phone number.
            first (int): Number of applications to fetch (default: 10).
            offset (int): The number of managers to skip (for pagination).

        Returns:

        Returns:
            list[Application]: A list of Application objects, or an empty list if none found.

        Logs:
            - INFO if no applications are found.
            - WARNING if sorting is applied to an invalid field.
        """

        query = ApplicationModel.query

        query = query.filter(ApplicationModel.is_deleted == False)

        total_count, total_closed_count, total_transferred_count, total_in_progress_count = cls._get_total_status_counts()

        branch_counts = cls._get_total_branch_counts(query)

        query = cls._apply_query_operations(query, filter, search, sort)

        all_applications = query.offset(offset).limit(first).all()

        if not all_applications:
            logger.info("No applications found with given criteria")
            return ApplicationConnection(applications=[])

        return ApplicationConnection(
            applications=[build_application_response(application) for application in all_applications],
            total_count=total_count,
            total_closed_count=total_closed_count,
            total_transferred_count=total_transferred_count,
            total_in_progress_count=total_in_progress_count,
            branch_counts=branch_counts
        )

    @classmethod
    @login_required(role="admin")
    def resolve_fetch_deleted_applications(cls, root, info, filter=None, sort=None, search=None, first=10, offset=0):
        """
        Resolves the query to fetch all soft-deleted applications (Admins only).

        Args:
            root (Any): GraphQL root argument (unused).
            info (ResolveInfo): GraphQL resolver context.
            filter (ApplicationFilterInput | None): Filters to apply.
            sort ([ApplicationSortInput] | None): Sorting criteria.
            search (str | None): Search term for client name or phone number.
            first (int): Number of applications to fetch (default: 10).
            offset (int): The number of applications to skip (for pagination).

        Returns:
            ApplicationConnection: A list of soft-deleted Application objects, or an empty list if none found.

        Logs:
            - INFO if no applications are found.
            - WARNING if sorting is applied to an invalid field.
        """
        query = ApplicationModel.query

        query = query.filter(ApplicationModel.is_deleted == True)

        query = cls._apply_query_operations(query, filter, search, sort)

        all_deleted_applications = query.offset(offset).limit(first).all()

        if not all_deleted_applications:
            logger.info("No deleted applications found with given criteria")
            return ApplicationConnection(applications=[])

        return ApplicationConnection(
            applications=[build_application_response(application) for application in all_deleted_applications]
        )

    @classmethod
    def _apply_query_operations(cls, query, filter, search, sort):
        """
        Applies filtering, searching, and sorting to the query.

        Args:
            query (Query): SQLAlchemy query object.
            filter (ApplicationFilterInput | None): Filters to apply.
            search (str | None): Search term for client name or phone number.
            sort ([ApplicationSortInput] | None): Sorting criteria.

        Returns:
            Query: Updated query with filters, search, and sorting applied.
        """
        if filter:
            query = cls._apply_filters(query, filter)

        if search:
            query = cls._apply_search(query, search)

        if sort:
            query = cls._apply_sort(query, sort)
        else:
            query = query.order_by(ApplicationModel.id.asc())

        return query

    @classmethod
    def _apply_filters(cls, query, filter):
        """
       Applies filtering criteria to the query.

       Args:
           query (Query): SQLAlchemy query object.
           filter (ApplicationFilterInput): Filter criteria.

       Returns:
           Query: Updated query with filters applied.
       """
        if filter.branch_name:
            try:
                query = query.filter(ApplicationModel.branch_name == filter.branch_name)
            except ValueError:
                logger.warning(f"Invalid branch_name: {filter.branch_name}")

        if filter.status:
            query = query.filter(ApplicationModel.status == filter.status)

        return query

    @classmethod
    def _apply_search(cls, query, search):
        """
        Searches applications by phone number.

        Args:
            query (Query): SQLAlchemy query object.
            search (str): Search term.

        Returns:
            Query: Updated query with search conditions.
        """
        search_term = f"%{search}%"
        return query.filter((ApplicationModel.phone_number.ilike(search_term)))

    @classmethod
    def _apply_sort(cls, query, sort):
        """
        Applies sorting criteria to the query.

        Args:
            query (Query): SQLAlchemy query object.
            sort (List[ApplicationSortInput]): Sorting criteria.

        Returns:
            Query: Updated query with sorting applied.

        Logs:
            - WARNING if an invalid sort field is used.
        """
        for sort_item in sort:
            if hasattr(ApplicationModel, sort_item.field):
                field = getattr(ApplicationModel, sort_item.field)
                query = query.order_by(field.desc() if sort_item.direction == SortDirection.DESC else field.asc())
            else:
                logger.warning(f"Invalid sort field: {sort_item.field}, ignoring.")

        return query

    @classmethod
    def _get_total_status_counts(cls):
        """
        Calculates total counts for all applications and by status.

        Returns:
            tuple: (total_count, total_closed_count, total_transferred_count, total_in_progress_count)
        """
        counts = db.session.query(
            func.count().label("total"),
            func.count(case((ApplicationModel.status == "closed", 1), else_=None)).label("closed"),
            func.count(case((ApplicationModel.status == "transferred", 1), else_=None)).label("transferred"),
            func.count(case((ApplicationModel.status == "in-progress", 1), else_=None)).label("in_progress")
        ).one()
        total_count, total_closed_count, total_transferred_count, total_in_progress_count = counts
        return total_count, total_closed_count, total_transferred_count, total_in_progress_count

    @classmethod
    def _get_total_branch_counts(cls, query):
        branch_counts_query = (
            query
            .group_by(ApplicationModel.branch_name)
            .with_entities(
                ApplicationModel.branch_name,
                func.count().label("count")
            )
            .all()
        )

        branch_counts = [
            BranchCount(branch=branch_name, count=count)
            for branch_name, count in branch_counts_query
        ]

        return branch_counts
