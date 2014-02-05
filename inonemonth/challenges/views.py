from django.http import HttpResponseRedirect, HttpResponseForbidden
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import user_passes_test
from django.core.urlresolvers import reverse_lazy
from django.shortcuts import render
from django.views.generic import DetailView
from django.forms.formsets import formset_factory

from rest_framework import generics

from core.models import UserExtension
from core.allauth_utils import create_allauth_user, generate_password
from comments.forms import HeadCommentForm, TailCommentForm
from comments.models import HeadComment, TailComment
from .forms import ChallengeCreateModelForm, JurorInviteForm
from .models import Challenge, Role, Vote
from .serializers import ChallengeSerializer, RoleSerializer
#!! from .decorators import user_has_profile


#!! @user_has_profile
def challenge_create_view(request):
    if request.method == "POST":
        form = ChallengeCreateModelForm(request.POST)
        if form.is_valid():
            # Get Profile based on username
            #!! profile = Profile.objects.get(user=request.user)

            # Save data to challenge
            model = form.instance.__class__
            cleaned_dic = form.cleaned_data
            inst = model.objects.create(**cleaned_dic)
            #!! inst = model.objects.create(clencher=profile, **cleaned_dic)
            # If Juror selection here done then also add jurors to model here.
            inst.save()
            #import pdb; pdb.set_trace()

            #return HttpResponseRedirect(reverse_lazy("challenge_detail_view",
            #                            kwargs={"pk": inst.pk}))
            return HttpResponseRedirect(reverse_lazy("challenge_invite_jurors_view",
                                        kwargs={"pk": inst.pk}))
    else:
        form = ChallengeCreateModelForm()

    return render(request=request, template_name='challenge/challenge_create.html',
                  dictionary={"form": form})


def invite_jurors_view(request, **kwargs):
    JurorInviteFormset = formset_factory(JurorInviteForm)
    challenge = Challenge.objects.get(pk=kwargs["pk"])
    if request.method == "POST":
        formset = JurorInviteFormset(request.POST)
        if formset.is_valid():
            clencher = Role.objects.create(user=request.user,
                                           challenge=challenge,
                                           type=Role.CLENCHER)

            for form in formset:
                password = generate_password()
                user = create_allauth_user(email=form.cleaned_data["email"],
                                           password=password)
                print password

                # hashed passwords can't be retrieved, so they'll need to be
                # stored somewhere to send that temporary password to the user.
                # The user can then change the password by himself later on.
                UserExtension.objects.create(user=user, temp_password=password)

                # Here, Send invitation email to user to challenge (probably need to
                # deactivate mailing email confirmation)
                juror = Role.objects.create(user=user, challenge=challenge,
                                            type=Role.JUROR)
                # Could also be created with celery, at moment juror period
                # starts
                #vote = Vote.objects.create(juror=juror)

            """
            model = form.instance.__class__
            #cleaned_dic.pop(field_name)  # If frm field not def in model
            inst = model.objects.create(**cleaned_dic)
            inst.save()
            """
            return HttpResponseRedirect(reverse_lazy("challenge_detail_view",
                                        kwargs={"pk": challenge.pk}))
    else:
        formset = JurorInviteFormset()

    return render(request=request, template_name='challenge/invite_jurors.html',
                  dictionary={"formset": formset, "model": challenge})


def challenge_detail_view(request, **kwargs):
    challenge = Challenge.objects.get(pk=kwargs["pk"])
    role = request.user.role_set.get(challenge=challenge)
    role_api_url = role.get_absolute_url()
    if request.method == "POST":
        head_comment_form = HeadCommentForm(request.POST)
        tail_comment_form = TailCommentForm(request.POST)

        # http://stackoverflow.com/questions/1395807/proper-way-to-handle-multiple-forms-on-one-page-in-django
        # http://stackoverflow.com/questions/866272/how-can-i-build-multiple-submit-buttons-django-form
        if "head-submit" in (head_comment_form.data or tail_comment_form.data):
            if head_comment_form.is_valid():
                head_comment_id = head_comment_form.data["id"]
                # In case of comment edit
                if head_comment_id:
                    # Check should be made if the head_comment is owned by the
                    # role
                    head_comment = HeadComment.objects.get(id=head_comment_id)
                    if head_comment.owner == role:
                        head_comment.challenge = challenge
                        head_comment.text = head_comment_form.cleaned_data["text"]
                        head_comment.save()

                        vote = Vote.objects.get(juror=role)
                        vote.decision = head_comment_form.cleaned_data["decision"]
                        vote.save()
                    else:
                        return HttpResponseForbidden()

                else:
                    HeadComment.objects.create(owner=role, challenge=challenge,
                                       text=head_comment_form.cleaned_data["text"])

                    Vote.objects.create(juror=role,
                                   decision=head_comment_form.cleaned_data["decision"])


        elif "tail-submit" in (head_comment_form.data or tail_comment_form.data):
            if tail_comment_form.is_valid():
                tail_comment_id = tail_comment_form.data["id"]
                # In case of comment edit
                if tail_comment_id:
                    tail_comment = TailComment.objects.get(id=tail_comment_id)
                    if tail_comment.owner == role:
                        tail_comment.challenge = challenge
                        tail_comment.text = tail_comment_form.cleaned_data["text"]
                        tail_comment.head = HeadComment.objects.get(id=int(tail_comment_form.data["head-id"]))
                        tail_comment.save()
                    else:
                        return HttpResponseForbidden()

                else:
                    TailComment.objects.create(owner=role, challenge=challenge,
                                           text=tail_comment_form.cleaned_data["text"],
                                           head=HeadComment.objects.get(id=int(tail_comment_form.data["head-id"])))

    else:
        head_comment_form = HeadCommentForm()
        tail_comment_form = TailCommentForm()

    return render(request=request, template_name='challenge/challenge_detail.html',
                  dictionary={"role_api_url": role_api_url,
                              "challenge": challenge,
                              "head_comment_form": head_comment_form,
                              "tail_comment_form": tail_comment_form
                              }
    )


class ChallengeRetrieveAPIView(generics.RetrieveAPIView):
    queryset = Challenge.objects.all()
    serializer_class = ChallengeSerializer


class RoleRetrieveAPIView(generics.RetrieveAPIView):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
