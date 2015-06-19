from django.test import TestCase
from django.db import models

from django_cereal.tests.testapp.models import ModelWithBasicField, ModelWithParentModel


class PickleTestCase(TestCase):

    def test_basic_patch(self):
        """Test that patching works as expected."""
        from django_cereal.pickle import model_encode, model_decode

        expected = ModelWithBasicField.objects.create(name='foo')
        actual = model_decode(model_encode(expected))

        self.assertGreater(expected.pk, 0)
        self.assertEqual(actual.pk, expected.pk)
        self.assertEqual(actual.name, 'foo')

    def test_deep_patch(self):
        """Test that models contained deep inside a dict are serialized correctly."""
        from django_cereal.pickle import model_encode, model_decode
        
        bar = ModelWithBasicField.objects.create(name='bar')
        eggs = ModelWithBasicField.objects.create(name='sausage')
        expected = {'foo': {'bar': bar,
                            'eggs': eggs}}
        actual = model_decode(model_encode(expected))

        self.assertEqual(actual, expected)

    def test_raises_on_doesnotexist(self):
        """Tests that decoding raises DoesNotExist if the item can't be found in the database."""
        from django_cereal.pickle import model_encode, model_decode

        dne = ModelWithBasicField(id=1)
        encoded = model_encode(dne)
        self.assertRaises(ModelWithBasicField.DoesNotExist, model_decode, encoded)

    def test_cleanup(self):
        """Test that the serialization cleans up after itself."""
        from django_cereal.pickle import model_encode, model_decode

        patched = ('__reduce__', '__setstate__', '__getstate__')
        expected = {}
        actual = {}
        for patch in patched:
            try:
                expected[patch] = getattr(models.Model, patch)
            except:
                expected[patch] = None

        m = ModelWithBasicField.objects.create(name='foo')
        model_decode(model_encode(m))

        for patch in patched:
            try:
                actual[patch] = getattr(models.Model, patch)
            except:
                actual[patch] = None

        for key, value in expected.items():
            self.assertIn(key, actual, 'Expected key %s to exist in actual' % key)
            self.assertEqual(actual[key], value, "Expected %s in actual to be equal to %s not %s." % (key, value, actual[key]))

    def test_inherited_model(self):
        """Test that patching an inherited models works as expected."""
        from django_cereal.pickle import model_encode, model_decode

        expected = ModelWithParentModel.objects.create(name='foo')
        actual = model_decode(model_encode(expected))

        self.assertGreater(expected.pk, 0)
        self.assertEqual(actual.pk, expected.pk)
        self.assertEqual(actual.name, 'foo')
