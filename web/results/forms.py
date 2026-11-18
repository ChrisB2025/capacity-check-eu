"""The reviewer feedback form."""

from django import forms

from web.results.models import Feedback

# The questions put to reviewers, as (field, question).
QUESTIONS = (
    ("question_right", "Is the question right? Is labour the right first "
     "resource to score, and is the shock a fair test?"),
    ("weakest", "Where is the method weakest?"),
    ("trust", "What would make you trust or distrust the output?"),
    ("who_else", "Who else should see this before it is published, and why?"),
    ("other", "Anything else"),
)  # fmt: skip


class FeedbackForm(forms.ModelForm):
    # Honeypot: hidden from people, filled in by bots. A filled form is
    # thanked and dropped.
    website = forms.CharField(required=False, label="Leave this empty")

    class Meta:
        model = Feedback
        fields = ["name", "organisation", "email", *[k for k, _ in QUESTIONS]]
        labels = {k: q for k, q in QUESTIONS} | {
            "name": "Your name (optional)",
            "organisation": "Organisation (optional)",
            "email": "Email, if you would like a reply (optional)",
        }
        widgets = {k: forms.Textarea(attrs={"rows": 4}) for k, _ in QUESTIONS}

    def clean(self):
        data = super().clean()
        if not any((data.get(k) or "").strip() for k, _ in QUESTIONS):
            raise forms.ValidationError("Please answer at least one question.")
        return data
