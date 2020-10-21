import Model, {Set} from './model';


export default class Sound extends Model {
    get name() { return this.data.name }
    get src() { return this.data.url }

    static getId(data) { return data.pk }
}


