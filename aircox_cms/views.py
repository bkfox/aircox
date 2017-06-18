#from django.shortcuts import render
#import django.views.generic as generic
#
#import foxcms.views as Views
#
#import aircox.sections as sections
#
#class DynamicListView(Views.View, generic.list.ListView):
#    list_info = None
#
#    def get_queryset(self):
#        self.list_info = {}
#        return sections.ListBase.from_request(request, context = self.list_info)
#
#    #def get_ordering(self):
#    #    order = self.request.GET.get('order_by')
#    #    if order:
#    #        field = order[1:] if order['-'] else order
#    #    else:
#    #        field = 'pk'
#    #    if field not in self.model.ordering_fields:
#    #        return super().get_ordering()
#    # TODO replace 'asc' in ListBase into sorting field
#
#    def get_context_data(self, *args, **kwargs
#        context = super().get_context_data(*args, **kwargs)
#        if self.list_info:
#            context.update(self.list_info)
#        return context




