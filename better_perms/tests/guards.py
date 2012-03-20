from better.perms.guards import DbGuard, Guard

class ArticleDbGuard(DbGuard):
    def check_read_obj(self, *args, **kwargs):
        return True


class ArticleGuard(Guard):
    def check_read_obj(self, *args, **kwargs):
        return True