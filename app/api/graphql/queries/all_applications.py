import logging

from sqlalchemy import case, func
from graphene import ObjectType, List, String, Argument, Int, ID, Field, Boolean

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

    fetch_all_application = Field(
        ApplicationConnection,
        filter=Argument(ApplicationFilterInput, description="Filter applications"),
        sort=Argument(List(ApplicationSortInput), description="Sort applications"),
        search=Argument(String, description="Search by client name or phone number"),
        first=Argument(Int, default_value=10, description="Number of applications to return"),
        after=Argument(ID, description="Cursor for fetching after this ID"),
        include_deleted=Argument(Boolean, default_value=False,
                                 description="Include soft-deleted applications (admin only)")

    )

    @classmethod
    def resolve_fetch_all_application(cls, root, info, filter=None, sort=None, search=None, first=10, after=None,
                                      include_deleted=False):
        """
        Resolves the query to fetch all Applications.

        Args:
            root (Any): GraphQL root argument (unused).
            info (ResolveInfo): GraphQL resolver context.
            filter (ApplicationFilterInput): Filters to apply.
            sort ([ApplicationSortInput]): Sort criteria.
            search (str): Search term for client name or phone number.
            first (int): Number of applications to fetch (default: 10).
            after (ID): Fetch applications after this ID (cursor-based pagination).

        Returns:

        Returns:
            list[Application]: A list of Application objects, or an empty list if none found.

        Logs:
            - INFO if no applications are found.
            - WARNING if sorting is applied to an invalid field.
        """
        # Check if user is a superuser
        # user = g.get('user')  # Adjust based on your auth system
        # is_superuser = user and getattr(user, 'is_superuser', False)

        # Only allow include_deleted if user is superuser
        # if not is_superuser:
        #     include_deleted = False

        query = ApplicationModel.query

        if not include_deleted:
            query = query.filter(ApplicationModel.is_deleted == False)

        (total_count,
         total_closed_count,
         total_transferred_count,
         total_in_progress_count) = cls._get_total_status_counts(query)

        branch_counts = cls._get_total_branch_counts(query)

        if filter:
            query = cls._apply_filters(query, filter)

        if search:
            query = cls._apply_search(query, search)

        if after:
            query = query.filter(ApplicationModel.id > int(after))

        if sort:
            query = cls._apply_sort(query, sort)
        else:
            query = query.order_by(ApplicationModel.id.asc())

        query = query.limit(first)

        all_applications = query.all()

        if not all_applications:
            logger.info("No applications found with given criteria")
            return ApplicationConnection(
                applications=[],
                total_count=total_count,
                total_closed_count=total_closed_count,
                total_transferred_count=total_transferred_count,
                total_in_progress_count=total_in_progress_count,
                branch_counts=branch_counts
            )

        return ApplicationConnection(
            applications=[build_application_response(application) for application in all_applications],
            total_count=total_count,
            total_closed_count=total_closed_count,
            total_transferred_count=total_transferred_count,
            total_in_progress_count=total_in_progress_count,
            branch_counts=branch_counts
        )

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
        if filter.branch_id:
            try:
                query = query.filter(ApplicationModel.branch_id == int(filter.branch_id))
            except ValueError:
                logger.warning(f"Invalid branch_id: {filter.branch_id}")

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
    def _get_total_status_counts(cls, query):
        """
        Calculates total counts for all applications and by status.

        Args:
            query (Query): SQLAlchemy query object.

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
            .group_by(ApplicationModel.branch_id)
            .with_entities(
                ApplicationModel.branch_id,
                func.count().label("count")
            )
            .all()
        )

        branch_counts = [
            BranchCount(branch_id=branch_id, count=count)
            for branch_id, count in branch_counts_query
        ]

        return branch_counts
