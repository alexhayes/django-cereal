# -*- coding: utf-8 -*-
"""
    django_cereal/pickle.py
    ~~~~~~~~~~~~~~~~~~~~~~~

    Efficient serializing of Django Models for use in Celery using pickle.

"""
from __future__ import absolute_import
import pickle
from contextlib import contextmanager

from django.db import models


__all__ = ['DJANGO_CEREAL_PICKLE', 'patched_model', 'model_encode',
           'model_decode', 'task', 'register_args']

DJANGO_CEREAL_PICKLE = 'django_cereal_pickle'


def _model_unpickle(cls, data):
    """Unpickle a model by retrieving it from the database."""
    auto_field_value = data['pk']
    obj = cls.objects.get(pk=auto_field_value)
    return obj
_model_unpickle.__safe_for_unpickle__ = True


def _reduce(self):
    cls = self.__class__
    data = {'pk': self.pk}
    return (_model_unpickle, (cls, data), data)


@contextmanager
def patched_model():
    """Context Manager that safely patches django.db.Model.__reduce__()."""

    patched = ('__reduce__', '__getstate__', '__setstate__')
    originals = {}
    for patch in patched:
        try:
            originals[patch] = getattr(models.Model, patch)
        except:
            pass

    try:
        # Patch various parts of the model
        models.Model.__reduce__ = _reduce
        try:
            del models.Model.__getstate__
        except:
            pass
        try:
            del models.Model.__setstate__
        except:  # pragma: no cover
            pass

        yield

    finally:
        # Restore the model
        for patch in patched:
            try:
                setattr(models.Model, patch, originals[patch])
            except KeyError:
                try:
                    delattr(models.Model, patch)
                except AttributeError:
                    pass


def model_encode(data):
    """Pickle data utilising the patched_model context manager."""
    with patched_model():
        return pickle.dumps(data)


def model_decode(data):
    """Unpickle data utilising the patched_model context manager."""

    # Note we must import here to avoid recursion issue with kombu entry points registration
    from kombu.serialization import unpickle

    with patched_model():
        return unpickle(data)


def task(func, *args, **kwargs):
    """
    A task decorator that uses the django-cereal pickler as the default serializer.
    """

    # Note we must import here to avoid recursion issue with kombu entry points registration
    from celery import shared_task

    if 'serializer' not in kwargs:
        kwargs['serializer'] = DJANGO_CEREAL_PICKLE
    return shared_task(func, *args, **kwargs)


register_args = (model_encode, model_decode,
                 'application/x-python-serialize', 'binary')
