from django.db.models import Q

from comments.models import CommentModel
from comments.schemas import CommentSchema


def build_comment_tree(roots: list[CommentModel]) -> list[CommentSchema]:
    """Serialize root comments and their descendants into nested DTOs."""
    if not roots:
        return []

    steplen = CommentModel.steplen

    cond = Q()
    for root in roots:
        cond |= Q(path__startswith=root.path)

    nodes = CommentModel.objects.filter(cond).select_related("user").order_by("path")

    by_path: dict[str, CommentSchema] = {}
    for node in nodes:
        uploaded_file = node.files.first()
        dto = CommentSchema(
            id=node.id,
            username=node.user.username,
            email=node.user.email,
            homepage=node.homepage,
            text=node.text,
            file_url=(
                uploaded_file.file.url
                if uploaded_file is not None and uploaded_file.processing_status == "processed"
                else None
            ),
            children=[],
        )
        by_path[node.path] = dto
        if node.depth > 1:
            by_path[node.path[:-steplen]].children.append(dto)

    return [by_path[root.path] for root in roots]
