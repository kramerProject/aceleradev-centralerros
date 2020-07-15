from django.core.validators import MinLengthValidator, EmailValidator, validate_ipv4_address
from django.db import models
import datetime
import rest_framework_jwt
import jwt

LEVEL_CHOICES = [
    ('critical', 'critical.'),
    ('debug', 'debug'),
    ('warning', 'warning'),
    ('information', 'info')
]

ENV_CHOICES = [
    ('Produção', 'Produção'),
    ('Homologação', 'Homologação'),
    ('Desenvolvimento', 'Desenvolvimento')
]


# Create your models here.

min_validator = MinLengthValidator(8, 'the password must have at least 8 characters')

class Group(models.Model):
    name = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']

class User(models.Model):
    name = models.CharField(max_length=50)
    email = models.EmailField(validators=[EmailValidator], null=True)
    password = models.CharField(max_length=500, validators=[min_validator])
    last_login = models.DateField(default=datetime.date.today)
    group = models.ManyToManyField(Group)

    def __str__(self):
        return f'{self.id} - {self.name}'

    def get_amount_users(self):
        return User.objects.count()

    def get_admin_users(self, group):
        return User.objects.filter(group__name=group)

    def set_password(self):
        payload = {'data': self.email}
        token = jwt.encode(payload,self.password, algorithm='HS256')
        return token


class Agent(models.Model):
    name = models.CharField(max_length=50)
    user = models.ForeignKey(User, on_delete=models.PROTECT, null=True)
    address = models.GenericIPAddressField(validators=[validate_ipv4_address], null=True)
    status = models.BooleanField(default=False)
    env = models.CharField(max_length=20, choices=ENV_CHOICES)
    version = models.CharField(max_length=20)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']

class Event(models.Model):
    user = models.ForeignKey(User, on_delete=models.PROTECT, null=True)
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES)
    data = models.TextField(max_length=500)
    agent = models.OneToOneField(Agent, on_delete=models.PROTECT)
    arquivado = models.BooleanField(default=False)
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.level + 'in' + self.agent.name

    class Meta:
        ordering = ['date']
