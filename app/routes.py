from app import app
from app import forms
from flask import render_template
from flask.views import MethodView
from googletrans import Translator
from models.model import interact_model


class ArticlesGenAPI(MethodView):
    template = 'index.html'
    context = {
        'title': 'Генератор определений',
    }
    translator = Translator()

    def get(self):
        self.context['form'] = forms.PhraseForm()
        self.context['message'] = ''
        self.context['text_samples'] = ''
        return render_template(self.template, **self.context)

    def post(self):
        form = forms.PhraseForm()
        if form.validate_on_submit():
            self.context['message'] = form.phrase.data
        else:
            self.context['message'] = 'blya'
        self.context['form'] = form
        phrase = self.translator.translate(form.phrase.data).text
        self.context['text_samples'] = [
            form.phrase.data + ' ' + self.translator.translate(text, dest='ru').text
            for text in interact_model(
                phrase,
                nsamples=form.samples_count.data,
                top_k=20,
                temperature=0.7)
        ]
        return render_template(self.template, **self.context)


app.add_url_rule('/',
                 view_func=ArticlesGenAPI.as_view('api'),
                 methods=['POST', 'GET'])
