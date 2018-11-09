from typing import List, Dict, Union

def get_sufficient_txos(sources: Dict[str,Dict[str,Union[int,str]]],
                        sovatoms: Union[str,int]) -> Dict[str, Union[Dict,int]]:
    result = {
       'txos': [],
       'change': 0
    }
    balance = int(sovatoms)
    extra = 0
    for txo, details in sources.items():
        if balance == 0:
            break
        if details['amount'] <= balance:
            # txo is entirely consumed. Decrease the balance by the amount in
            # the txo.
            balance -= details['amount']
            # Add the txo to the list of txos, expecting it to be completely
            # consumed
            result['txos'].append(txo)
        else:
            # The txo is only partially consumed. Add the txo to the list of
            # txos to use and calculate the change left over.
            result['txos'].append(txo)
            # txo is only partly consumed. Give the change.
            result['change'] = (details['amount'] - balance)
            balance = 0
         
    return result
# End helper functions
