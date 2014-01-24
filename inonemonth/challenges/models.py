from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist


class Challenge(models.Model):
    """
    """
    # Use placeholder: one line description of what you want to achieve
    title = models.CharField(max_length=200)
    body = models.TextField()
    repo_name = models.CharField(max_length=200)
    creation_datetime = models.DateTimeField(auto_now_add=True)

    # Don"t include self.role_set.user because the user will not exist
    # in some cases.
    def __unicode__(self):
        return "Challenge {0}, created on {1}".format(
            self.id,
            self.creation_datetime.ctime()
        )

    def get_clencher(self):
        try:
            return self.role_set.get(type=self.role_set.model.CLENCHER)
        except ObjectDoesNotExist:
            raise Exception("No user has been assigned as clencher "
                                  "for this challenge yet.")

    def get_jurors(self):
        # `filter` call with no results returns an empty list (vs `get`)
        jurors = self.role_set.filter(type=self.role_set.model.JUROR)
        if jurors:
            return jurors
        else:
            return self.Exception("No Juror has been assigned as juror "
                                     "for this challenge yet.")


class Role(models.Model):
    """
    Role for a given challenge: Clencher or Juror.
    A role instance for a given challenge is attached to one user at maximum.
    """
    CLENCHER = "clencher" # is more descriptive than a single capital in js
    JUROR = "juror"
    ROLE_CHOICES = ((CLENCHER, CLENCHER.capitalize()),
                    (JUROR, JUROR.capitalize()))

    user = models.ForeignKey(get_user_model())
    type = models.CharField(max_length=10, choices=ROLE_CHOICES)
    challenge = models.ForeignKey(Challenge)

    def __unicode__(self):
        return "{0} '{1}' of '{2}'".format(self.type.capitalize(), self.user, self.challenge)


class JurorVote(models.Model):
    """
    Vote if challenge is deemed successful or not by a juror for a given challenge.
    """
    POSITIVE = "positive"
    NEGATIVE = "negative"
    DECISION_CHOICES = ((POSITIVE, POSITIVE), (NEGATIVE, NEGATIVE))

    decision = models.CharField(max_length=10, choices=DECISION_CHOICES, default="")
    juror = models.OneToOneField(Role) # only use for jurors!

    def __unicode__(self):
        return "{0} vote of {1}".format(self.decision, self.juror)
