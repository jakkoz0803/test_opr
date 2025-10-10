from django.test import TestCase
from django.utils import timezone
from django.urls import reverse
from .models import Question

# --------------------------
# Testy modeli
# --------------------------
class QuestionModelTests(TestCase):

    def test_was_published_recently_with_future_question(self):
        """
        was_published_recently() powinno zwrócić False dla pytania z przyszłości.
        """
        future_question = Question(
            question_text="Pytanie z przyszłości",
            pub_date=timezone.now() + timezone.timedelta(days=5)
        )
        self.assertIs(future_question.was_published_recently(), False)

    def test_was_published_recently_with_past_question(self):
        """
        was_published_recently() powinno zwrócić True dla pytania z ostatnich 24h.
        """
        past_question = Question(
            question_text="Pytanie z przeszłości",
            pub_date=timezone.now() - timezone.timedelta(hours=5)
        )
        self.assertIs(past_question.was_published_recently(), True)


# --------------------------
# Testy widoków
# --------------------------
class QuestionViewTests(TestCase):

    def setUp(self):
        """
        Tworzymy dwa pytania w bazie testowej
        """
        self.past_question = Question.objects.create(
            question_text="Pytanie przeszłe",
            pub_date=timezone.now() - timezone.timedelta(days=1)
        )
        self.future_question = Question.objects.create(
            question_text="Pytanie przyszłe",
            pub_date=timezone.now() + timezone.timedelta(days=1)
        )

    def test_index_view_only_shows_past_questions(self):
        """
        Widok indeksu powinien wyświetlać tylko pytania z przeszłości
        """
        response = self.client.get(reverse('polls:index'))
        self.assertQuerySetEqual(
            response.context['latest_question_list'],
            ['Pytanie przeszłe'],
            transform=lambda q: q.question_text
        )

    def test_index_view_with_no_questions(self):
        """
        Jeśli nie ma pytań, lista powinna być pusta
        """
        # Usuwamy wszystkie pytania
        Question.objects.all().delete()
        response = self.client.get(reverse('polls:index'))
        self.assertQuerySetEqual(response.context['latest_question_list'], [])

    def test_index_view_multiple_past_questions(self):
        """
        Jeśli jest kilka pytań z przeszłości, wszystkie powinny się wyświetlać
        """
        Question.objects.create(
            question_text="Drugie pytanie przeszłe",
            pub_date=timezone.now() - timezone.timedelta(hours=2)
        )
        response = self.client.get(reverse('polls:index'))
        self.assertQuerySetEqual(
            response.context['latest_question_list'],
            ['Drugie pytanie przeszłe', 'Pytanie przeszłe'],
            transform=lambda q: q.question_text
        )
