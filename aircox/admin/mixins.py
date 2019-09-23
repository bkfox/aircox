class UnrelatedInlineMixin:
    """
    Inline class that can be included in an admin change view whose model
    is not directly related to inline's model.
    """
    view_model = None
    parent_model = None
    parent_fk = ''

    def __init__(self, parent_model, admin_site):
        self.view_model = parent_model
        super().__init__(self.parent_model, admin_site)

    def get_parent(self, view_obj):
        """ Get formset's instance from `obj` of AdminSite's change form. """
        field = self.parent_model._meta.get_field(self.parent_fk).remote_field
        return getattr(view_obj, field.name, None)

    def save_parent(self, parent, view_obj):
        """ Save formset's instance. """
        setattr(parent, self.parent_fk, view_obj)
        parent.save()
        return parent

    def get_formset(self, request, obj):
        ParentFormSet = super().get_formset(request, obj)
        inline = self
        class FormSet(ParentFormSet):
            view_obj = None

            def __init__(self, *args, instance=None, **kwargs):
                self.view_obj = instance
                instance = inline.get_parent(instance)
                self.instance = instance
                super().__init__(*args, instance=instance, **kwargs)

            def save(self):
                inline.save_parent(self.instance, self.view_obj)
                return super().save()
        return FormSet


