# -*- coding: utf-8 -*-
from openprocurement.api.utils import (
    json_view, context_unpack, get_now
)
from openprocurement.tender.core.utils import (
    save_tender, apply_patch, optendersresource
)
from openprocurement.tender.core.validation import (
    validate_lot_data, validate_patch_lot_data
)
from openprocurement.tender.openua.views.lot import (
    TenderUaLotResource as TenderLotResource
)


@optendersresource(name='negotiation.quick:Tender Lots',
                   collection_path='/tenders/{tender_id}/lots',
                   path='/tenders/{tender_id}/lots/{lot_id}',
                   procurementMethodType='negotiation.quick',
                   description="Tender limited negotiation quick lots")
class TenderLimitedNegotiationQuickLotResource(TenderLotResource):
    route_name = 'Tender limited negotiation quick Lots'

    def validate_update_tender(self, operation):
        tender = self.request.validated['tender']
        if tender.status != 'active':
            self.request.errors.add('body', 'data', 'Can\'t {} lot in current ({}) tender status'.format(
                operation, tender.status))
            self.request.errors.status = 403
            return
        if tender.awards:
            self.request.errors.add('body', 'data', 'Can\'t {} lot when you have awards'.format(
                operation, tender.status))
            self.request.errors.status = 403
            return
        return True

    @json_view(content_type="application/json", validators=(validate_lot_data,), permission='edit_tender')
    def collection_post(self):
        """Add a lot
        """
        if not self.validate_update_tender('add'):
            return
        lot = self.request.validated['lot']
        lot.date = get_now()
        tender = self.request.validated['tender']
        tender.lots.append(lot)
        if save_tender(self.request):
            self.LOGGER.info('Created tender lot {}'.format(lot.id),
                             extra=context_unpack(self.request, {'MESSAGE_ID': 'tender_lot_create'},
                                                  {'lot_id': lot.id}))
            self.request.response.status = 201
            self.request.response.headers['Location'] = self.request.route_url('{}:Tender Lots'.format(tender.procurementMethodType),
                                                                               tender_id=tender.id, lot_id=lot.id)
            return {'data': lot.serialize("view")}

    @json_view(content_type="application/json", validators=(validate_patch_lot_data,), permission='edit_tender')
    def patch(self):
        """Update of lot
        """
        if not self.validate_update_tender('update'):
            return
        tender = self.request.validated['tender']
        lot = self.request.context
        if [cancellation for cancellation in tender.get('cancellations') if cancellation.get('relatedLot') == lot['id']]:
            self.request.errors.add('body', 'data', 'Can\'t update lot when it has \'pending\' cancellation.')
            self.request.errors.status = 403
            return
        if apply_patch(self.request, src=self.request.context.serialize()):
            self.LOGGER.info('Updated tender lot {}'.format(self.request.context.id),
                             extra=context_unpack(self.request, {'MESSAGE_ID': 'tender_lot_patch'}))
            return {'data': self.request.context.serialize("view")}

    @json_view(permission='edit_tender')
    def delete(self):
        """Lot deleting
        """
        if not self.validate_update_tender('delete'):
            return
        lot = self.request.context
        res = lot.serialize("view")
        tender = self.request.validated['tender']
        tender.lots.remove(lot)
        if save_tender(self.request):
            self.LOGGER.info('Deleted tender lot {}'.format(self.request.context.id),
                             extra=context_unpack(self.request, {'MESSAGE_ID': 'tender_lot_delete'}))
            return {'data': res}


@optendersresource(name='negotiation:Tender Lots',
                   collection_path='/tenders/{tender_id}/lots',
                   path='/tenders/{tender_id}/lots/{lot_id}',
                   procurementMethodType='negotiation',
                   description="Tender limited negotiation lots")
class TenderLimitedNegotiationLotResource(TenderLimitedNegotiationQuickLotResource):
    route_name = 'Tender limited negotiation Lots'
